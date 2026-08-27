"""Extract the on-page SEO surface from HTML, using html.parser from the stdlib.

This is the module that replaces "the model reads the page and tells you what
the title is". Same input, same output, every time, and a test can pin it.

Deliberately not a browser: no JavaScript is executed. A page that renders its
title client-side reports `requires_js: true` rather than a wrong answer, and
the caller can decide whether that matters.
"""
from __future__ import annotations

import json
import re
from html import unescape
from html.parser import HTMLParser
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlsplit

# Text inside these never reaches a reader, so it never counts as content.
INVISIBLE = {"script", "style", "template", "noscript", "svg", "head", "title"}
# Wrappers that surround content rather than being it. Used to estimate the
# main content area when no <main> or <article> is present.
CHROME = {"nav", "header", "footer", "aside", "form"}

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_SPA_ROOT = re.compile(
    r"<(?:div|main)[^>]+id\s*=\s*[\"\']?(?:root|app|__next|__nuxt|q-app)[\"\']?", re.I
)


def count_words(text: str) -> int:
    """Words a reader would count: letter runs, so numbers and punctuation do not inflate it."""
    return len(_WORD.findall(text or ""))


class PageParser(HTMLParser):
    """Collects the SEO surface in a single pass."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: List[str] = []
        self.metas: List[Dict[str, str]] = []
        self.links: List[Dict[str, str]] = []
        self.headings: List[Dict[str, object]] = []
        self.images: List[Dict[str, str]] = []
        self.anchors: List[Dict[str, str]] = []
        self.jsonld_raw: List[str] = []
        self.html_lang: Optional[str] = None
        self.has_main = False
        self.has_article = False
        self.has_viewport = False
        self.text_parts: List[str] = []
        self.main_text_parts: List[str] = []
        self._invisible_depth = 0
        self._chrome_depth = 0
        self._main_depth = 0
        self._in_title = False
        self._in_jsonld = False
        self._jsonld_buffer: List[str] = []
        self._heading: Optional[Dict[str, object]] = None
        self._anchor: Optional[Dict[str, str]] = None

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _attrs(pairs) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for key, value in pairs:
            if key is not None:
                out[key.lower()] = (value or "").strip()
        return out

    # -- tag handling ----------------------------------------------------

    def _separate(self) -> None:
        """Insert a space at a child-element boundary inside a heading or link.

        Markup like <h1><span>Be the team</span><span>suppliers love</span></h1>
        has no whitespace between the spans, so naive concatenation produces
        "Be the teamsuppliers love". A reader sees two phrases, so the extracted
        text has to as well.
        """
        if self._heading is not None:
            self._heading["text"] = str(self._heading["text"]) + " "
        if self._anchor is not None:
            self._anchor["text"] += " "

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attributes = self._attrs(attrs)
        if tag not in ("h1", "h2", "h3", "h4", "h5", "h6", "a"):
            self._separate()

        if tag == "html":
            self.html_lang = attributes.get("lang") or None
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            self.metas.append(attributes)
            if attributes.get("name", "").lower() == "viewport":
                self.has_viewport = True
        elif tag == "link":
            self.links.append(attributes)
        elif tag == "img":
            self.images.append(
                {
                    "src": attributes.get("src", ""),
                    "alt": attributes.get("alt"),
                    "loading": attributes.get("loading", ""),
                    "width": attributes.get("width", ""),
                    "height": attributes.get("height", ""),
                }
            )
        elif tag == "a":
            self._anchor = {"href": attributes.get("href", ""), "rel": attributes.get("rel", ""), "text": ""}
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading = {"level": int(tag[1]), "text": "", "id": attributes.get("id", "")}
        elif tag == "script" and "ld+json" in attributes.get("type", "").lower():
            self._in_jsonld = True
            self._jsonld_buffer = []
        elif tag == "main":
            self.has_main = True
            self._main_depth += 1
        elif tag == "article":
            self.has_article = True
            if not self.has_main:
                self._main_depth += 1

        if tag in INVISIBLE:
            self._invisible_depth += 1
        if tag in CHROME:
            self._chrome_depth += 1

    def handle_startendtag(self, tag, attrs):
        # Self-closing form: run the start handler, then undo any depth it added.
        tag_low = tag.lower()
        self.handle_starttag(tag, attrs)
        if tag_low in INVISIBLE:
            self._invisible_depth -= 1
        if tag_low in CHROME:
            self._chrome_depth -= 1
        if tag_low in ("main", "article"):
            self._main_depth = max(0, self._main_depth - 1)
        if tag_low == "a":
            self._anchor = None
        if tag_low in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading = None

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag not in ("h1", "h2", "h3", "h4", "h5", "h6", "a"):
            self._separate()
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_jsonld:
            self.jsonld_raw.append("".join(self._jsonld_buffer))
            self._in_jsonld = False
            self._jsonld_buffer = []
        elif tag == "a" and self._anchor is not None:
            self._anchor["text"] = " ".join(self._anchor["text"].split())
            self.anchors.append(self._anchor)
            self._anchor = None
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._heading is not None:
            self._heading["text"] = " ".join(str(self._heading["text"]).split())
            self.headings.append(self._heading)
            self._heading = None
        elif tag in ("main", "article"):
            self._main_depth = max(0, self._main_depth - 1)

        if tag in INVISIBLE:
            self._invisible_depth = max(0, self._invisible_depth - 1)
        if tag in CHROME:
            self._chrome_depth = max(0, self._chrome_depth - 1)

    def close(self):
        """Flush nodes still open at end of document.

        Real pages ship unclosed tags. If a heading whose </h1> never arrives is
        simply dropped, the audit reports "no H1" on a page that has one, which
        is worse than reporting the heading with imperfect text.
        """
        super().close()
        if self._heading is not None:
            self._heading["text"] = " ".join(str(self._heading["text"]).split())
            if self._heading["text"]:
                self.headings.append(self._heading)
            self._heading = None
        if self._anchor is not None:
            self._anchor["text"] = " ".join(self._anchor["text"].split())
            self.anchors.append(self._anchor)
            self._anchor = None
        if self._in_jsonld and self._jsonld_buffer:
            self.jsonld_raw.append("".join(self._jsonld_buffer))
            self._in_jsonld = False
            self._jsonld_buffer = []

    def handle_data(self, data):
        if self._in_jsonld:
            self._jsonld_buffer.append(data)
            return
        if self._in_title:
            self.title_parts.append(data)
            return
        if self._heading is not None:
            self._heading["text"] = str(self._heading["text"]) + data
        if self._anchor is not None:
            self._anchor["text"] += data
        if self._invisible_depth:
            return
        stripped = data.strip()
        if not stripped:
            return
        self.text_parts.append(stripped)
        if self._main_depth or not self._chrome_depth:
            self.main_text_parts.append(stripped)


def _first_meta(metas: List[Dict[str, str]], key: str, value: str) -> Optional[str]:
    for meta in metas:
        if meta.get(key, "").lower() == value:
            content = meta.get("content")
            return content if content is not None else ""
    return None


def _all_meta(metas: List[Dict[str, str]], key: str, prefix: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for meta in metas:
        name = meta.get(key, "").lower()
        if name.startswith(prefix):
            out[name] = meta.get("content", "")
    return out


def parse_page(html: str, url: str = "") -> Dict[str, object]:
    """Return the on-page SEO surface of one HTML document.

    `url` is used to resolve relative links and to split internal from external
    anchors. Pass the final URL after redirects, not the requested one.
    """
    parser = PageParser()
    try:
        parser.feed(html or "")
        parser.close()
    except Exception as exc:  # malformed markup is a finding, not a crash
        return {
            "ok": False,
            "error": "could not parse HTML: {}: {}".format(type(exc).__name__, exc),
            "url": url,
        }

    metas = parser.metas
    title = " ".join("".join(parser.title_parts).split()) or None
    host = (urlsplit(url).hostname or "").lower()

    canonical = None
    hreflang: List[Dict[str, str]] = []
    amphtml = None
    for link in parser.links:
        rels = link.get("rel", "").lower().split()
        href = link.get("href", "")
        if "canonical" in rels and canonical is None:
            canonical = urljoin(url, href) if url else href
        if "alternate" in rels and link.get("hreflang"):
            hreflang.append(
                {"hreflang": link["hreflang"], "href": urljoin(url, href) if url else href}
            )
        if "amphtml" in rels:
            amphtml = urljoin(url, href) if url else href

    internal = external = nofollow = 0
    for anchor in parser.anchors:
        href = anchor.get("href", "")
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        target_host = (urlsplit(urljoin(url, href)).hostname or "").lower() if url else ""
        if not target_host or target_host == host:
            internal += 1
        else:
            external += 1
        if "nofollow" in anchor.get("rel", "").lower():
            nofollow += 1

    schema_blocks: List[Dict[str, object]] = []
    for index, raw in enumerate(parser.jsonld_raw):
        text = raw.strip()
        if not text:
            continue
        try:
            schema_blocks.append({"index": index, "valid_json": True, "data": json.loads(text)})
        except json.JSONDecodeError as exc:
            schema_blocks.append(
                {
                    "index": index,
                    "valid_json": False,
                    "error": "invalid JSON at line {} column {}: {}".format(
                        exc.lineno, exc.colno, exc.msg
                    ),
                    "raw_preview": text[:200],
                }
            )

    body_text = " ".join(parser.text_parts)
    main_text = " ".join(parser.main_text_parts)
    images_missing_alt = [
        img["src"] for img in parser.images if img.get("alt") is None or img.get("alt") == ""
    ]

    robots = _first_meta(metas, "name", "robots")
    return {
        "ok": True,
        "url": url,
        "title": title,
        "title_length": len(title) if title else 0,
        "meta_description": _first_meta(metas, "name", "description"),
        "meta_robots": robots,
        "meta_robots_directives": [d.strip().lower() for d in robots.split(",")] if robots else [],
        "canonical": canonical,
        "canonical_is_self": (
            None if not (canonical and url) else canonical.rstrip("/") == url.rstrip("/")
        ),
        "html_lang": parser.html_lang,
        "hreflang": hreflang,
        "amphtml": amphtml,
        "has_viewport": parser.has_viewport,
        "headings": parser.headings,
        "h1": [h["text"] for h in parser.headings if h["level"] == 1],
        "h2": [h["text"] for h in parser.headings if h["level"] == 2],
        "h3": [h["text"] for h in parser.headings if h["level"] == 3],
        "open_graph": _all_meta(metas, "property", "og:"),
        "twitter": _all_meta(metas, "name", "twitter:"),
        "schema_blocks": schema_blocks,
        "schema_types": sorted(
            {
                str(t)
                for block in schema_blocks
                if block.get("valid_json")
                for t in _schema_types(block.get("data"))
            }
        ),
        "word_count": count_words(body_text),
        "main_word_count": count_words(main_text),
        "text_preview": body_text[:400],
        "images": len(parser.images),
        "images_missing_alt": len(images_missing_alt),
        "images_missing_alt_examples": images_missing_alt[:10],
        "links_internal": internal,
        "links_external": external,
        "links_nofollow": nofollow,
        "requires_js": bool(_SPA_ROOT.search(html or "")) and count_words(main_text) < 100,
    }


def _schema_types(data) -> List[str]:
    """Every @type in a JSON-LD block, including inside @graph and nested nodes."""
    found: List[str] = []
    if isinstance(data, dict):
        raw = data.get("@type")
        if isinstance(raw, str):
            found.append(raw)
        elif isinstance(raw, list):
            found.extend(str(item) for item in raw)
        for value in data.values():
            found.extend(_schema_types(value))
    elif isinstance(data, list):
        for item in data:
            found.extend(_schema_types(item))
    return found


def strip_tags(html: str) -> str:
    """Visible text of a fragment, for word counts on content supplied inline."""
    parser = PageParser()
    parser.feed(html or "")
    parser.close()
    return unescape(" ".join(parser.text_parts))
