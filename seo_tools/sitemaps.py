"""Sitemap discovery and parsing, including index files and gzip.

Answers the question /indexation-check needs: what does the site claim it
wants indexed, and does that set agree with what is actually reachable.
"""
from __future__ import annotations

import gzip
import io
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

from .fetching import fetch
from .robots import RobotsTxt, robots_url_for

# Sitemaps live at conventional paths often enough that guessing is worth a
# few requests when robots.txt declares nothing.
COMMON_PATHS = (
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/sitemap.xml.gz",
    "/wp-sitemap.xml",
    "/sitemap/sitemap.xml",
    "/sitemaps/sitemap.xml",
)
MAX_URLS_PER_SITEMAP = 50000
MAX_BYTES_UNCOMPRESSED = 50 * 1024 * 1024


def _strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def parse_sitemap(body: bytes, url: str = "") -> Dict[str, object]:
    """Parse one sitemap or sitemap index. Handles gzip transparently."""
    payload = body
    if body[:2] == b"\x1f\x8b" or url.endswith(".gz"):
        try:
            payload = gzip.GzipFile(fileobj=io.BytesIO(body)).read(MAX_BYTES_UNCOMPRESSED)
        except OSError as exc:
            return {"ok": False, "url": url, "error": "gzip decode failed: {}".format(exc)}
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        return {"ok": False, "url": url, "error": "XML parse failed: {}".format(exc)}

    kind = _strip_namespace(root.tag)
    entries: List[Dict[str, object]] = []
    for child in root:
        if _strip_namespace(child.tag) not in ("url", "sitemap"):
            continue
        entry: Dict[str, object] = {}
        for field in child:
            name = _strip_namespace(field.tag)
            if name in ("loc", "lastmod", "changefreq", "priority"):
                entry[name] = (field.text or "").strip()
        if entry.get("loc"):
            entries.append(entry)

    return {
        "ok": True,
        "url": url,
        "kind": "sitemapindex" if kind == "sitemapindex" else "urlset",
        "entries": entries,
        "count": len(entries),
        "over_limit": len(entries) > MAX_URLS_PER_SITEMAP,
    }


def discover(site_url: str, allow_private: bool = False) -> Dict[str, object]:
    """Find the sitemaps for a site: robots.txt declarations, then conventions."""
    split = urlsplit(site_url)
    origin = "{}://{}".format(split.scheme, split.netloc)
    found: List[Dict[str, object]] = []
    declared: List[str] = []

    robots_result = fetch(robots_url_for(site_url), allow_private=allow_private)
    robots_ok = bool(robots_result.get("ok"))
    if robots_ok:
        parsed = RobotsTxt(
            str(robots_result.get("text") or ""),
            int(robots_result.get("status") or 200),
            url=str(robots_result.get("final_url") or ""),
        )
        declared = list(parsed.sitemaps)

    checked: Set[str] = set()
    for candidate in declared + [urljoin(origin, path) for path in COMMON_PATHS]:
        if candidate in checked:
            continue
        checked.add(candidate)
        result = fetch(candidate, allow_private=allow_private)
        if not result.get("ok"):
            found.append(
                {
                    "url": candidate,
                    "declared_in_robots": candidate in declared,
                    "reachable": False,
                    "error": result.get("error"),
                }
            )
            continue
        status = int(result.get("status") or 0)
        if status != 200:
            found.append(
                {
                    "url": candidate,
                    "declared_in_robots": candidate in declared,
                    "reachable": False,
                    "status": status,
                }
            )
            continue
        parsed_map = parse_sitemap(bytes(result.get("body") or b""), candidate)
        found.append(
            {
                "url": candidate,
                "declared_in_robots": candidate in declared,
                "reachable": True,
                "status": status,
                "kind": parsed_map.get("kind"),
                "count": parsed_map.get("count"),
                "valid_xml": parsed_map.get("ok"),
                "error": parsed_map.get("error"),
                "entries": parsed_map.get("entries") if parsed_map.get("ok") else [],
            }
        )
        # A declared sitemap that works is enough; stop probing conventions.
        if candidate in declared and parsed_map.get("ok"):
            continue

    reachable = [f for f in found if f.get("reachable")]
    stale_declarations = [
        f["url"] for f in found if f.get("declared_in_robots") and not f.get("reachable")
    ]
    return {
        "site": origin,
        "robots_reachable": robots_ok,
        "declared_in_robots": declared,
        "stale_declarations": stale_declarations,
        "sitemaps": found,
        "reachable_count": len(reachable),
        "total_urls": sum(int(f.get("count") or 0) for f in reachable if f.get("kind") == "urlset"),
    }


def expand(discovery: Dict[str, object], allow_private: bool = False, limit: int = 5000) -> Dict[str, object]:
    """Walk a sitemap index one level down and collect the URL set."""
    urls: List[Dict[str, object]] = []
    child_maps: List[Dict[str, object]] = []
    seen: Set[str] = set()

    for sitemap in discovery.get("sitemaps") or []:
        if not sitemap.get("reachable") or not sitemap.get("valid_xml"):
            continue
        if sitemap.get("kind") == "sitemapindex":
            for entry in sitemap.get("entries") or []:
                loc = str(entry.get("loc"))
                if loc in seen:
                    continue
                seen.add(loc)
                result = fetch(loc, allow_private=allow_private)
                if not result.get("ok") or int(result.get("status") or 0) != 200:
                    child_maps.append({"url": loc, "reachable": False, "status": result.get("status")})
                    continue
                parsed = parse_sitemap(bytes(result.get("body") or b""), loc)
                child_maps.append(
                    {
                        "url": loc,
                        "reachable": True,
                        "count": parsed.get("count"),
                        "valid_xml": parsed.get("ok"),
                    }
                )
                for child in parsed.get("entries") or []:
                    if len(urls) >= limit:
                        break
                    urls.append(child)
        else:
            for entry in sitemap.get("entries") or []:
                if len(urls) >= limit:
                    break
                urls.append(entry)

    unique = []
    seen_loc: Set[str] = set()
    duplicates = 0
    for entry in urls:
        loc = str(entry.get("loc"))
        if loc in seen_loc:
            duplicates += 1
            continue
        seen_loc.add(loc)
        unique.append(entry)

    with_lastmod = sum(1 for e in unique if e.get("lastmod"))
    return {
        "child_sitemaps": child_maps,
        "urls": unique,
        "url_count": len(unique),
        "duplicates": duplicates,
        "with_lastmod": with_lastmod,
        "lastmod_coverage_pct": round(with_lastmod / len(unique) * 100, 1) if unique else None,
        "truncated_at": limit if len(urls) >= limit else None,
    }
