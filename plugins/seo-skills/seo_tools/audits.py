"""Deterministic on-page checks over a parsed page.

Every function here takes the dict from parsing.parse_page and returns findings
as data: an id, a severity, what was observed, and what to do. No prose, no
model in the loop. A skill reads these findings and decides what is worth the
reader's attention, which is the part a model should be doing.

Severities are fixed: `critical` costs traffic now, `warning` probably costs
traffic, `info` is worth knowing. Nothing here guesses at a ranking effect,
per PRINCIPLES.md.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from . import typography

Finding = Dict[str, object]

# Schema.org types and the properties Google documents as required for the
# corresponding rich result. Keeping this narrow and dated beats a long list
# that nobody maintains.
SCHEMA_REQUIRED: Dict[str, List[str]] = {
    "Article": ["headline"],
    "NewsArticle": ["headline"],
    "BlogPosting": ["headline"],
    "Product": ["name"],
    "Offer": ["price", "priceCurrency"],
    "FAQPage": ["mainEntity"],
    "Question": ["name", "acceptedAnswer"],
    "HowTo": ["name", "step"],
    "Recipe": ["name", "recipeIngredient", "recipeInstructions"],
    "Event": ["name", "startDate", "location"],
    "JobPosting": ["title", "description", "datePosted", "hiringOrganization"],
    "LocalBusiness": ["name", "address"],
    "Organization": ["name"],
    "BreadcrumbList": ["itemListElement"],
    "VideoObject": ["name", "thumbnailUrl", "uploadDate"],
    "SoftwareApplication": ["name"],
}

# Types Google has retired as rich result drivers. Emitting them is not an
# error, but expecting a rich result from them is.
SCHEMA_RETIRED: Dict[str, str] = {
    "HowTo": "Google dropped HowTo rich results for desktop and mobile in 2023. Valid markup, no rich result.",
    "FAQPage": "Since August 2023 Google shows FAQ rich results only for well-known health and government sites.",
    "Book": "Book actions are limited to approved partners.",
    "Course": "Course rich results need a Course carousel and an approved provider feed.",
}


def _finding(check: str, severity: str, message: str, **extra) -> Finding:
    out: Finding = {"check": check, "severity": severity, "message": message}
    out.update(extra)
    return out


def check_meta(page: Dict[str, object]) -> List[Finding]:
    """Title and description: presence, width, duplication against H1.

    Every pass or fail decision here is made in pixels, never in characters.
    A character count is not comparable across scripts: a 28-character Japanese
    title fills more of the SERP than a 45-character English one, so a character
    floor reports the Japanese title as too short while it is nearly full.
    Character counts are still reported, because that is what briefs are written
    against.
    """
    findings: List[Finding] = []
    title = page.get("title")
    description = page.get("meta_description")

    if not title:
        findings.append(
            _finding("title.missing", "critical", "No title tag. Google will invent one from the page.")
        )
    else:
        measured = typography.measure_title(str(title))
        blocked = typography.unmeasurable_scripts(str(title))
        if blocked:
            # Width cannot be summed per character for these scripts, so a
            # truncation verdict would be a pass or fail on a number that does
            # not mean what it looks like. Say that instead of deciding.
            findings.append(
                _finding(
                    "title.width_unmeasurable",
                    "info",
                    "Cannot measure this title's width reliably: {}. Check it against a "
                    "live result page instead of trusting a pixel figure.".format(
                        ", ".join("{} is {}".format(b["script"], b["reason"]) for b in blocked)
                    ),
                    observed=title,
                    chars=measured["chars"],
                    px_floor=measured["px"],
                    method=measured["method"],
                )
            )
        elif measured["truncates"]:
            findings.append(
                _finding(
                    "title.too_wide",
                    "warning",
                    "Title is an estimated {} px against a {} px limit, so it truncates.".format(
                        measured["px"], measured["px_limit"]
                    ),
                    observed=title,
                    px=measured["px"],
                    chars=measured["chars"],
                    preview=measured["truncated_preview"],
                    method=measured["method"],
                )
            )
        if (
            not blocked
            and measured["px_used_pct"] is not None
            and measured["px_used_pct"] < typography.MIN_FILL_PCT
        ):
            findings.append(
                _finding(
                    "title.short",
                    "warning",
                    "Title uses {}% of the available width, under the {}% floor, so it is "
                    "leaving room unused.".format(
                        measured["px_used_pct"], typography.MIN_FILL_PCT
                    ),
                    observed=title,
                    px=measured["px"],
                    chars=measured["chars"],
                    method=measured["method"],
                )
            )

    if description is None:
        findings.append(
            _finding(
                "description.missing",
                "warning",
                "No meta description. Google will pull a snippet from the body, which you do not control.",
            )
        )
    elif not str(description).strip():
        findings.append(
            _finding("description.empty", "warning", "Meta description tag is present but empty.")
        )
    else:
        measured = typography.measure_description(str(description))
        if measured["truncates"]:
            findings.append(
                _finding(
                    "description.too_wide",
                    "info",
                    "Description is an estimated {} px against a {} px limit, so the tail is cut.".format(
                        measured["px"], measured["px_limit"]
                    ),
                    observed=description,
                    px=measured["px"],
                    chars=measured["chars"],
                    preview=measured["truncated_preview"],
                    method=measured["method"],
                )
            )
        if measured["px_used_pct"] is not None and measured["px_used_pct"] < typography.MIN_FILL_PCT:
            findings.append(
                _finding(
                    "description.short",
                    "info",
                    "Description uses {}% of the available width, under the {}% floor.".format(
                        measured["px_used_pct"], typography.MIN_FILL_PCT
                    ),
                    observed=description,
                    px=measured["px"],
                    chars=measured["chars"],
                )
            )

    h1s = page.get("h1") or []
    if title and h1s and str(title).strip().lower() == str(h1s[0]).strip().lower():
        findings.append(
            _finding(
                "title.duplicates_h1",
                "info",
                "Title and H1 are identical, which wastes the chance to target a second phrasing.",
                observed=title,
            )
        )
    return findings


def check_headings(page: Dict[str, object]) -> List[Finding]:
    """H1 count and heading hierarchy. Skipped levels break the outline."""
    findings: List[Finding] = []
    headings = page.get("headings") or []
    h1s = page.get("h1") or []

    if not h1s:
        findings.append(_finding("h1.missing", "critical", "No H1 on the page."))
    elif len(h1s) > 1:
        findings.append(
            _finding(
                "h1.multiple",
                "warning",
                "{} H1 elements. Valid HTML5, but it splits the page's stated subject.".format(len(h1s)),
                observed=h1s,
            )
        )

    for heading in headings:
        if not str(heading.get("text", "")).strip():
            findings.append(
                _finding(
                    "heading.empty",
                    "warning",
                    "An H{} is empty, usually an icon or image with no text alternative.".format(
                        heading.get("level")
                    ),
                    level=heading.get("level"),
                )
            )

    previous: Optional[int] = None
    for heading in headings:
        level = int(heading.get("level", 0))
        if previous is not None and level > previous + 1:
            findings.append(
                _finding(
                    "heading.level_skipped",
                    "info",
                    "H{} follows H{}, skipping a level.".format(level, previous),
                    observed=heading.get("text"),
                    level=level,
                    previous_level=previous,
                )
            )
        previous = level
    return findings


def check_indexability(page: Dict[str, object], headers: Optional[Dict[str, str]] = None) -> List[Finding]:
    """Whether the page is telling search engines to keep it out of the index."""
    findings: List[Finding] = []
    directives = [d.lower() for d in (page.get("meta_robots_directives") or [])]
    header_robots = ""
    if headers:
        header_robots = str(
            headers.get("x-robots-tag") or headers.get("X-Robots-Tag") or ""
        ).lower()

    if "noindex" in directives:
        findings.append(
            _finding(
                "robots.noindex_meta",
                "critical",
                "meta robots says noindex. Intentional on a thank-you page, fatal on a landing page.",
                observed=page.get("meta_robots"),
            )
        )
    if "noindex" in header_robots:
        findings.append(
            _finding(
                "robots.noindex_header",
                "critical",
                "X-Robots-Tag header says noindex, which is easy to miss because it is not in the HTML.",
                observed=header_robots,
            )
        )
    if "nofollow" in directives:
        findings.append(
            _finding(
                "robots.nofollow_meta",
                "warning",
                "meta robots says nofollow, so no link equity leaves this page.",
                observed=page.get("meta_robots"),
            )
        )
    if not page.get("canonical"):
        findings.append(
            _finding(
                "canonical.missing",
                "warning",
                "No canonical link. Any parameter variant of this URL competes with it.",
            )
        )
    elif page.get("canonical_is_self") is False:
        findings.append(
            _finding(
                "canonical.points_elsewhere",
                "info",
                "Canonical points to a different URL, so this URL is asking not to be the indexed one.",
                observed=page.get("canonical"),
                url=page.get("url"),
            )
        )
    if page.get("requires_js"):
        findings.append(
            _finding(
                "rendering.requires_js",
                "warning",
                "Almost no text in the served HTML next to an app root element. The content is likely "
                "client-rendered, so anything that does not execute JavaScript sees an empty page.",
                main_word_count=page.get("main_word_count"),
            )
        )
    if not page.get("has_viewport"):
        findings.append(
            _finding("mobile.no_viewport", "warning", "No viewport meta tag, so mobile rendering is unmanaged.")
        )
    if not page.get("html_lang"):
        findings.append(
            _finding("lang.missing", "info", "No lang attribute on the html element.")
        )
    return findings


def check_schema(page: Dict[str, object]) -> List[Finding]:
    """JSON-LD: parses, has a type, has the properties the type needs."""
    findings: List[Finding] = []
    blocks = page.get("schema_blocks") or []

    if not blocks:
        findings.append(
            _finding("schema.none", "info", "No JSON-LD structured data on the page.")
        )
        return findings

    for block in blocks:
        if not block.get("valid_json"):
            findings.append(
                _finding(
                    "schema.invalid_json",
                    "critical",
                    "A JSON-LD block does not parse, so every engine ignores it: {}".format(
                        block.get("error")
                    ),
                    index=block.get("index"),
                    preview=block.get("raw_preview"),
                )
            )
            continue
        for node in _nodes(block.get("data")):
            types = _types_of(node)
            if not types:
                continue
            for type_name in types:
                for required in SCHEMA_REQUIRED.get(type_name, []):
                    if required not in node:
                        findings.append(
                            _finding(
                                "schema.missing_required",
                                "warning",
                                "{} is missing the required property {!r}.".format(type_name, required),
                                type=type_name,
                                property=required,
                                index=block.get("index"),
                            )
                        )
                if type_name in SCHEMA_RETIRED:
                    findings.append(
                        _finding(
                            "schema.no_rich_result",
                            "info",
                            SCHEMA_RETIRED[type_name],
                            type=type_name,
                            index=block.get("index"),
                        )
                    )
    return findings


def check_images(page: Dict[str, object]) -> List[Finding]:
    """Alt coverage, stated as a count rather than a lecture."""
    findings: List[Finding] = []
    total = int(page.get("images") or 0)
    missing = int(page.get("images_missing_alt") or 0)
    if total and missing:
        findings.append(
            _finding(
                "images.missing_alt",
                "warning" if missing / total > 0.25 else "info",
                "{} of {} images have no alt text.".format(missing, total),
                missing=missing,
                total=total,
                examples=page.get("images_missing_alt_examples"),
            )
        )
    return findings


ALL_CHECKS = ("meta", "headings", "indexability", "schema", "images")


def audit_page(page: Dict[str, object], headers: Optional[Dict[str, str]] = None) -> Dict[str, object]:
    """Run every check and return findings plus a count by severity."""
    findings: List[Finding] = []
    findings.extend(check_meta(page))
    findings.extend(check_headings(page))
    findings.extend(check_indexability(page, headers))
    findings.extend(check_schema(page))
    findings.extend(check_images(page))

    order = {"critical": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda f: (order.get(str(f.get("severity")), 9), str(f.get("check"))))
    counts = {level: 0 for level in order}
    for finding in findings:
        counts[str(finding["severity"])] = counts.get(str(finding["severity"]), 0) + 1
    return {"findings": findings, "counts": counts, "total": len(findings)}


def _nodes(data) -> List[Dict]:
    """Flatten a JSON-LD payload into the dict nodes it contains."""
    out: List[Dict] = []
    if isinstance(data, dict):
        out.append(data)
        for key, value in data.items():
            if key == "@context":
                continue
            out.extend(_nodes(value))
    elif isinstance(data, list):
        for item in data:
            out.extend(_nodes(item))
    return out


def _types_of(node: Dict) -> List[str]:
    raw = node.get("@type")
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw]
    return []
