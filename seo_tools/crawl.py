"""Read a crawl export and normalise it, whoever produced it.

The point of this module is that the pack needs crawl data and does not care
where it comes from. Screaming Frog, Sitebulb, Semrush Site Audit, Ahrefs Site
Audit, Sitemap-driven or a spreadsheet someone assembled by hand all describe the
same thing: a list of URLs with a status, a title, a canonical and some structure.
So they are all mapped onto one row shape, and every analysis downstream reads
that shape rather than a vendor's column names.

That is what makes the provider swappable. Nothing here is Screaming Frog
specific, and adding a new exporter means adding aliases, not code.

Standard library only, like the rest of the package.
"""
from __future__ import annotations

import csv
import io
import pathlib
import re
from typing import Dict, List, Optional, Sequence

from .safety import normalise_url

# How many example URLs a grouped finding carries. The group's size is always
# reported in full as `count`; this bounds only the illustrative list.
URL_SAMPLE = 20

# The canonical row. Every exporter is mapped onto these names, and every
# analysis below reads only these.
CANONICAL_FIELDS = (
    "url",
    "status",
    "content_type",
    "indexability",
    "indexability_status",
    "title",
    "meta_description",
    "h1",
    "h2",
    "canonical",
    "meta_robots",
    "x_robots_tag",
    "word_count",
    "crawl_depth",
    "inlinks",
    "outlinks",
    "redirect_url",
    "size_bytes",
    "response_ms",
    "last_modified",
    "language",
)

# Column aliases, lowercased and squeezed. Screaming Frog and Sitebulb lead, but
# the names are matched loosely enough that a hand-built spreadsheet with
# sensible headers works too.
COLUMN_ALIASES: Dict[str, Sequence[str]] = {
    "url": ("address", "url", "urls", "page", "page url", "full url", "uri", "location"),
    "status": ("status code", "status", "http status", "http status code", "response code", "code"),
    "content_type": ("content type", "content-type", "mime type", "type"),
    "indexability": ("indexability", "indexable", "is indexable"),
    "indexability_status": ("indexability status", "indexability reason", "non-indexable reason"),
    "title": ("title 1", "title", "page title", "title tag", "meta title", "title 1 "),
    "meta_description": (
        "meta description 1", "meta description", "description", "meta description tag",
    ),
    "h1": ("h1-1", "h1 1", "h1", "h1 tag", "first h1"),
    "h2": ("h2-1", "h2 1", "h2", "h2 tag", "first h2"),
    "canonical": (
        "canonical link element 1", "canonical link element", "canonical", "canonical url",
        "canonical tag", "rel canonical",
    ),
    "meta_robots": ("meta robots 1", "meta robots", "robots", "robots meta"),
    "x_robots_tag": ("x-robots-tag 1", "x-robots-tag", "x robots tag"),
    "word_count": ("word count", "words", "word-count", "content word count"),
    "crawl_depth": ("crawl depth", "depth", "click depth", "level"),
    "inlinks": ("inlinks", "unique inlinks", "internal inlinks", "incoming links", "internal links"),
    "outlinks": ("outlinks", "unique outlinks", "internal outlinks", "outgoing links"),
    "redirect_url": ("redirect url", "redirect uri", "redirects to", "destination url"),
    "size_bytes": ("size (bytes)", "size", "size bytes", "page size", "html size"),
    "response_ms": ("response time", "response time (s)", "response ms", "load time"),
    "last_modified": ("last modified", "last-modified", "lastmod", "modified"),
    "language": ("language", "html lang", "lang", "content language"),
}

INTEGER_FIELDS = ("status", "word_count", "crawl_depth", "inlinks", "outlinks", "size_bytes")

# Signatures that identify who wrote the file. Used for the report header only:
# the mapping does not depend on getting this right.
EXPORTER_SIGNATURES = (
    ("Screaming Frog", ("address", "indexability status")),
    ("Screaming Frog", ("address", "title 1")),
    ("Sitebulb", ("url", "crawl depth", "indexable")),
    ("Semrush Site Audit", ("page url", "issues")),
    ("Ahrefs Site Audit", ("url", "http status code")),
)

_SQUEEZE = re.compile(r"[^a-z0-9]+")


class CrawlError(ValueError):
    """Raised when a file cannot be read as a crawl export."""


def _squeeze(text: str) -> str:
    return " ".join(_SQUEEZE.sub(" ", (text or "").strip().lower()).split())


def _canonical_column(raw: str) -> Optional[str]:
    squeezed = _squeeze(raw)
    if not squeezed:
        return None
    for field, aliases in COLUMN_ALIASES.items():
        if squeezed in tuple(_squeeze(a) for a in aliases):
            return field
    return None


def _to_int(value) -> Optional[int]:
    if value is None or value == "":
        return None
    text = str(value).strip().replace(",", "").replace(" ", "")
    match = re.match(r"^-?\d+", text)
    return int(match.group(0)) if match else None


def _truthy(value) -> Optional[bool]:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip().lower()
    if text in ("yes", "true", "1", "indexable"):
        return True
    if text in ("no", "false", "0", "non-indexable", "not indexable"):
        return False
    return None


def detect_exporter(header: Sequence[str]) -> str:
    squeezed = {_squeeze(cell) for cell in header}
    for name, markers in EXPORTER_SIGNATURES:
        if all(_squeeze(m) in squeezed for m in markers):
            return name
    return "unknown exporter"


def load_crawl(path: str, columns: Optional[str] = None) -> Dict[str, object]:
    """Read a crawl export into canonical rows.

    `columns` is the positional override, same idea as the one on `gsc`: name the
    columns in order, `-` to skip, for an exporter whose headers are not
    recognised. A crawl file with no recognisable URL column is refused, because
    every analysis here is keyed on the URL.
    """
    file_path = pathlib.Path(path)
    if not file_path.is_file():
        raise CrawlError("no such file: {}".format(path))
    raw = file_path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise CrawlError("could not decode {} as text".format(path))

    sample = text[:8192]
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        counts = {d: sample.count(d) for d in (",", ";", "\t")}
        delimiter = max(counts, key=lambda d: counts[d]) if any(counts.values()) else ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    header: List[str] = []
    for row in reader:
        if any(str(cell).strip() for cell in row):
            header = row
            break
    if not header:
        raise CrawlError("{} is empty".format(path))

    if columns:
        mapping = _parse_override(columns, len(header))
        resolved_by = "the --columns override"
    else:
        mapping = {}
        for index, cell in enumerate(header):
            field = _canonical_column(cell)
            if field and field not in mapping.values():
                mapping[index] = field
        resolved_by = "header names"

    if "url" not in mapping.values():
        raise CrawlError(
            "no URL column found in {}. Header was: {}. Name the columns positionally "
            "with --columns url,status,title,... (use - to skip one).".format(
                path, ", ".join(header[:8])
            )
        )

    rows: List[Dict[str, object]] = []
    for values in reader:
        if not any(str(v).strip() for v in values):
            continue
        row: Dict[str, object] = {field: None for field in CANONICAL_FIELDS}
        for index, field in mapping.items():
            if index >= len(values):
                continue
            cell = str(values[index]).strip()
            if field in INTEGER_FIELDS:
                row[field] = _to_int(cell)
            elif field == "indexability":
                row[field] = _truthy(cell)
            else:
                row[field] = cell or None
        if row.get("url"):
            rows.append(row)

    return {
        "path": str(file_path),
        "exporter": detect_exporter(header),
        "delimiter": delimiter,
        "columns_resolved_by": resolved_by,
        "columns_detected": sorted(set(mapping.values())),
        "columns_ignored": [
            header[i] for i in range(len(header)) if i not in mapping and str(header[i]).strip()
        ],
        "row_count": len(rows),
        "rows": rows,
    }


def _parse_override(spec: str, header_length: int) -> Dict[int, str]:
    names = [part.strip().lower().replace("-", "_") for part in (spec or "").split(",")]
    mapping: Dict[int, str] = {}
    for index, name in enumerate(names):
        if not name or name == "_":
            continue
        if name not in CANONICAL_FIELDS:
            raise CrawlError(
                "unknown column {!r}. Valid names: {}".format(name, ", ".join(CANONICAL_FIELDS))
            )
        if index >= header_length:
            raise CrawlError(
                "--columns names {} columns but the file has {}".format(len(names), header_length)
            )
        mapping[index] = name
    if not mapping:
        raise CrawlError("--columns did not name any usable column")
    return mapping


# -- analyses ------------------------------------------------------------


def summarise(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Counts a reader needs before any finding makes sense."""
    by_status: Dict[str, int] = {}
    indexable = non_indexable = unknown_index = 0
    depths: List[int] = []
    for row in rows:
        status = row.get("status")
        band = "{}xx".format(str(status)[0]) if status else "unknown"
        by_status[band] = by_status.get(band, 0) + 1
        flag = row.get("indexability")
        if flag is True:
            indexable += 1
        elif flag is False:
            non_indexable += 1
        else:
            unknown_index += 1
        depth = row.get("crawl_depth")
        if isinstance(depth, int):
            depths.append(depth)
    return {
        "urls": len(rows),
        "by_status_band": dict(sorted(by_status.items())),
        "indexable": indexable,
        "non_indexable": non_indexable,
        "indexability_unknown": unknown_index,
        "max_crawl_depth": max(depths) if depths else None,
        "median_crawl_depth": sorted(depths)[len(depths) // 2] if depths else None,
    }


def duplicates(rows: Sequence[Dict[str, object]], field: str) -> List[Dict[str, object]]:
    """URLs sharing an identical title, description or H1, worst offenders first.

    Only indexable 200 pages count. A duplicate title across two redirects or a
    noindexed pair is not a finding, and reporting it buries the ones that are.
    """
    groups: Dict[str, List[str]] = {}
    for row in rows:
        if row.get("status") not in (200, None) or row.get("indexability") is False:
            continue
        value = row.get(field)
        if not value:
            continue
        groups.setdefault(str(value).strip(), []).append(str(row["url"]))
    # The URL list is capped so a duplicate group covering a thousand pages does
    # not dump a thousand strings into the output. The cap is named rather than
    # silent: a live agent run read len(urls) as the size of the group and
    # understated a 31-page finding as 20. `count` is the truth, and
    # `urls_truncated` says when the list is not.
    out = [
        {
            "value": value,
            "count": len(urls),
            "urls": urls[:URL_SAMPLE],
            "urls_truncated": len(urls) > URL_SAMPLE,
            "urls_shown": min(len(urls), URL_SAMPLE),
        }
        for value, urls in groups.items()
        if len(urls) > 1
    ]
    out.sort(key=lambda g: g["count"], reverse=True)
    return out


def missing(rows: Sequence[Dict[str, object]], field: str) -> List[str]:
    """Indexable 200 pages with nothing in `field`."""
    return [
        str(row["url"])
        for row in rows
        if row.get("status") in (200, None)
        and row.get("indexability") is not False
        and not row.get(field)
    ]


def orphans(rows: Sequence[Dict[str, object]]) -> List[str]:
    """Indexable pages nothing links to, which the crawl only saw via a sitemap."""
    return [
        str(row["url"])
        for row in rows
        if row.get("inlinks") == 0
        and row.get("status") in (200, None)
        and row.get("indexability") is not False
    ]


def thin(rows: Sequence[Dict[str, object]], threshold: int = 300) -> List[Dict[str, object]]:
    """Indexable pages under a word threshold, shallowest first.

    The threshold is an argument and not a rule. A pricing page at 200 words can
    be exactly right, so this is a list to look at rather than a list to fix.
    """
    out = [
        {"url": str(row["url"]), "word_count": row["word_count"], "crawl_depth": row.get("crawl_depth")}
        for row in rows
        if isinstance(row.get("word_count"), int)
        and row["word_count"] < threshold
        and row.get("status") in (200, None)
        and row.get("indexability") is not False
    ]
    out.sort(key=lambda r: r["word_count"])
    return out


def non_self_canonical(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Pages whose canonical points somewhere else, which is often unintended."""
    out = []
    for row in rows:
        canonical = row.get("canonical")
        if not canonical:
            continue
        try:
            same = normalise_url(str(row["url"])) == normalise_url(str(canonical))
        except ValueError:
            same = str(row["url"]).rstrip("/") == str(canonical).rstrip("/")
        if not same:
            out.append({"url": str(row["url"]), "canonical": str(canonical), "status": row.get("status")})
    return out


def redirect_chains(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Redirects whose target is itself a redirect, within this crawl."""
    by_url = {}
    for row in rows:
        try:
            by_url[normalise_url(str(row["url"]))] = row
        except ValueError:
            by_url[str(row["url"])] = row

    chains = []
    for row in rows:
        status = row.get("status")
        target = row.get("redirect_url")
        if not (isinstance(status, int) and 300 <= status < 400 and target):
            continue
        try:
            key = normalise_url(str(target))
        except ValueError:
            key = str(target)
        next_row = by_url.get(key)
        next_status = next_row.get("status") if next_row else None
        if isinstance(next_status, int) and 300 <= next_status < 400:
            chains.append(
                {
                    "url": str(row["url"]),
                    "status": status,
                    "redirects_to": str(target),
                    "then_status": next_status,
                    "then_to": next_row.get("redirect_url"),
                }
            )
    return chains


def broken(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """URLs the crawl could not fetch, with their inlink count so severity is visible."""
    out = [
        {"url": str(row["url"]), "status": row.get("status"), "inlinks": row.get("inlinks")}
        for row in rows
        if isinstance(row.get("status"), int) and row["status"] >= 400
    ]
    out.sort(key=lambda r: (r["inlinks"] is None, -(r["inlinks"] or 0)))
    return out


def analyse(rows: Sequence[Dict[str, object]], thin_threshold: int = 300) -> Dict[str, object]:
    """Everything the crawl can answer on its own, with no API and no network."""
    return {
        "summary": summarise(rows),
        "broken": broken(rows),
        "redirect_chains": redirect_chains(rows),
        "duplicate_titles": duplicates(rows, "title"),
        "duplicate_descriptions": duplicates(rows, "meta_description"),
        "duplicate_h1": duplicates(rows, "h1"),
        "missing_titles": missing(rows, "title"),
        "missing_descriptions": missing(rows, "meta_description"),
        "missing_h1": missing(rows, "h1"),
        "non_self_canonical": non_self_canonical(rows),
        "orphans": orphans(rows),
        "thin": thin(rows, thin_threshold),
        "thin_threshold": thin_threshold,
    }
