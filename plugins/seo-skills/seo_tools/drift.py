"""Compare a page against a stored baseline and classify what changed.

The severity of a change is not the size of the change. A title rewrite is a
warning because it is usually deliberate. A canonical that appeared overnight
is critical because nobody does that on purpose. That judgement is what these
rules encode, and encoding it here rather than in a prompt is the point: the
same change produces the same severity every time, and the rule that fired is
named in the output so a reader can disagree with it.
"""
from __future__ import annotations

from typing import Dict, List, Optional

Change = Dict[str, object]

# Word count moving by less than this is normal editing, not drift.
WORD_COUNT_TOLERANCE_PCT = 10


def _change(rule: str, severity: str, field: str, before, after, note: str) -> Change:
    return {
        "rule": rule,
        "severity": severity,
        "field": field,
        "before": before,
        "after": after,
        "note": note,
    }


def _as_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def compare(baseline: Dict[str, object], current: Dict[str, object]) -> Dict[str, object]:
    """Diff a baseline snapshot against a freshly parsed page.

    `baseline` is the dict stored by store.save_baseline. `current` is a page
    dict from parsing.parse_page, with `status` added by the caller.
    """
    before = baseline.get("snapshot") or {}
    changes: List[Change] = []

    # -- status ----------------------------------------------------------
    old_status = before.get("status")
    new_status = current.get("status")
    if old_status != new_status:
        severity = "info"
        if isinstance(new_status, int) and new_status >= 400:
            severity = "critical"
        elif isinstance(new_status, int) and 300 <= new_status < 400:
            severity = "warning"
        changes.append(
            _change(
                "status.changed",
                severity,
                "status",
                old_status,
                new_status,
                "The page used to answer {} and now answers {}.".format(old_status, new_status),
            )
        )

    # -- indexability ----------------------------------------------------
    old_robots = str(before.get("meta_robots") or "").lower()
    new_robots = str(current.get("meta_robots") or "").lower()
    if "noindex" in new_robots and "noindex" not in old_robots:
        changes.append(
            _change(
                "robots.noindex_added",
                "critical",
                "meta_robots",
                before.get("meta_robots"),
                current.get("meta_robots"),
                "noindex appeared. This page is now asking to be dropped from the index.",
            )
        )
    elif "noindex" in old_robots and "noindex" not in new_robots:
        changes.append(
            _change(
                "robots.noindex_removed",
                "info",
                "meta_robots",
                before.get("meta_robots"),
                current.get("meta_robots"),
                "noindex was removed, so the page is now indexable.",
            )
        )
    elif old_robots != new_robots:
        changes.append(
            _change(
                "robots.changed",
                "warning",
                "meta_robots",
                before.get("meta_robots"),
                current.get("meta_robots"),
                "Robots directives changed.",
            )
        )

    old_canonical = before.get("canonical")
    new_canonical = current.get("canonical")
    if old_canonical != new_canonical:
        if old_canonical and not new_canonical:
            changes.append(
                _change(
                    "canonical.removed",
                    "critical",
                    "canonical",
                    old_canonical,
                    None,
                    "The canonical link is gone, so parameter variants can now compete with this URL.",
                )
            )
        elif not old_canonical and new_canonical:
            changes.append(
                _change(
                    "canonical.added",
                    "warning",
                    "canonical",
                    None,
                    new_canonical,
                    "A canonical appeared. Confirm it points where you expect.",
                )
            )
        else:
            changes.append(
                _change(
                    "canonical.changed",
                    "critical",
                    "canonical",
                    old_canonical,
                    new_canonical,
                    "The canonical target moved, which redirects indexing signals to a different URL.",
                )
            )

    # -- the visible snippet ---------------------------------------------
    if before.get("title") != current.get("title"):
        severity = "critical" if not current.get("title") else "warning"
        changes.append(
            _change(
                "title.changed",
                severity,
                "title",
                before.get("title"),
                current.get("title"),
                "Title is gone." if not current.get("title") else "Title was rewritten.",
            )
        )
    if before.get("meta_description") != current.get("meta_description"):
        severity = "warning" if not current.get("meta_description") else "info"
        changes.append(
            _change(
                "description.changed",
                severity,
                "meta_description",
                before.get("meta_description"),
                current.get("meta_description"),
                "Meta description is gone."
                if not current.get("meta_description")
                else "Meta description was rewritten.",
            )
        )

    # -- structure -------------------------------------------------------
    old_h1 = _as_list(before.get("h1"))
    new_h1 = _as_list(current.get("h1"))
    if old_h1 != new_h1:
        severity = "critical" if old_h1 and not new_h1 else "warning"
        changes.append(
            _change(
                "h1.changed",
                severity,
                "h1",
                old_h1,
                new_h1,
                "The H1 is gone." if not new_h1 else "The H1 changed.",
            )
        )
    for level in ("h2", "h3"):
        old = _as_list(before.get(level))
        new = _as_list(current.get(level))
        if old != new:
            removed = [h for h in old if h not in new]
            added = [h for h in new if h not in old]
            changes.append(
                _change(
                    "{}.changed".format(level),
                    "info",
                    level,
                    old,
                    new,
                    "{} removed, {} added at {}.".format(len(removed), len(added), level.upper()),
                )
            )

    # -- structured data -------------------------------------------------
    old_types = set(_as_list(before.get("schema_types")))
    new_types = set(_as_list(current.get("schema_types")))
    if old_types != new_types:
        lost = sorted(old_types - new_types)
        gained = sorted(new_types - old_types)
        if lost:
            changes.append(
                _change(
                    "schema.types_removed",
                    "critical",
                    "schema_types",
                    sorted(old_types),
                    sorted(new_types),
                    "Structured data types disappeared: {}. Any rich result they drove goes with them.".format(
                        ", ".join(lost)
                    ),
                )
            )
        if gained:
            changes.append(
                _change(
                    "schema.types_added",
                    "info",
                    "schema_types",
                    sorted(old_types),
                    sorted(new_types),
                    "New structured data types: {}.".format(", ".join(gained)),
                )
            )

    # -- content volume --------------------------------------------------
    old_words = before.get("main_word_count") or before.get("word_count") or 0
    new_words = current.get("main_word_count") or current.get("word_count") or 0
    if old_words and new_words:
        delta_pct = (new_words - old_words) / old_words * 100
        if abs(delta_pct) > WORD_COUNT_TOLERANCE_PCT:
            severity = "warning" if delta_pct < -25 else "info"
            changes.append(
                _change(
                    "content.volume_changed",
                    severity,
                    "main_word_count",
                    old_words,
                    new_words,
                    "Main content moved {:+.0f} percent, from {} words to {}.".format(
                        delta_pct, old_words, new_words
                    ),
                )
            )
    elif old_words and not new_words:
        changes.append(
            _change(
                "content.disappeared",
                "critical",
                "main_word_count",
                old_words,
                new_words,
                "The page had {} words of content and now has none in the served HTML.".format(old_words),
            )
        )

    # -- rendering -------------------------------------------------------
    if not before.get("requires_js") and current.get("requires_js"):
        changes.append(
            _change(
                "rendering.became_client_side",
                "critical",
                "requires_js",
                False,
                True,
                "Content used to be in the served HTML and now is not. Anything that does not run "
                "JavaScript, including most AI crawlers, now sees an empty page.",
            )
        )

    # -- social ----------------------------------------------------------
    old_og = before.get("open_graph") or {}
    new_og = current.get("open_graph") or {}
    if isinstance(old_og, dict) and isinstance(new_og, dict) and old_og != new_og:
        lost_keys = sorted(set(old_og) - set(new_og))
        changes.append(
            _change(
                "open_graph.changed",
                "warning" if lost_keys else "info",
                "open_graph",
                old_og,
                new_og,
                "Open Graph tags removed: {}.".format(", ".join(lost_keys))
                if lost_keys
                else "Open Graph values changed.",
            )
        )

    # -- links -----------------------------------------------------------
    old_internal = int(before.get("links_internal") or 0)
    new_internal = int(current.get("links_internal") or 0)
    if old_internal and new_internal < old_internal * 0.5:
        changes.append(
            _change(
                "links.internal_halved",
                "warning",
                "links_internal",
                old_internal,
                new_internal,
                "Internal links dropped from {} to {}, which changes what this page passes on.".format(
                    old_internal, new_internal
                ),
            )
        )

    order = {"critical": 0, "warning": 1, "info": 2}
    changes.sort(key=lambda c: (order.get(str(c["severity"]), 9), str(c["rule"])))
    counts = {"critical": 0, "warning": 0, "info": 0}
    for change in changes:
        counts[str(change["severity"])] = counts.get(str(change["severity"]), 0) + 1

    return {
        "url": current.get("url") or baseline.get("url"),
        "baseline_id": baseline.get("baseline_id"),
        "baseline_captured_at": baseline.get("captured_at"),
        "changes": changes,
        "counts": counts,
        "total_changes": len(changes),
        "verdict": _verdict(counts),
    }


def _verdict(counts: Dict[str, int]) -> str:
    if counts.get("critical"):
        return "regression: {} critical change(s) since the baseline".format(counts["critical"])
    if counts.get("warning"):
        return "review: {} change(s) worth checking".format(counts["warning"])
    if counts.get("info"):
        return "changed, nothing critical"
    return "no change against the baseline"


RULES = (
    "status.changed",
    "robots.noindex_added",
    "robots.noindex_removed",
    "robots.changed",
    "canonical.removed",
    "canonical.added",
    "canonical.changed",
    "title.changed",
    "description.changed",
    "h1.changed",
    "h2.changed",
    "h3.changed",
    "schema.types_removed",
    "schema.types_added",
    "content.volume_changed",
    "content.disappeared",
    "rendering.became_client_side",
    "open_graph.changed",
    "links.internal_halved",
)
