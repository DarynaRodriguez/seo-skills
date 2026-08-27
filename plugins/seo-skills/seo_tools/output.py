"""Rendering. Two audiences: a skill reading JSON, and a person reading a terminal.

Windows consoles default to a code page that cannot print most of what an SEO
audit contains, so stdout is reconfigured to UTF-8 on import. That single line
is why this package runs the same on Windows as it does on a Mac.
"""
from __future__ import annotations

import datetime
import json
import sys
from typing import Dict, List, Optional

SEVERITY_MARK = {"critical": "[!]", "warning": "[~]", "info": "[i]"}


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


configure_stdout()


def checked_at() -> str:
    """Now, as a full ISO 8601 instant in UTC.

    Every report the agents write carries a "when was this true" field, and no
    tool used to return one, so three separate live runs each invented their own:
    one shelled out to `date`, one used the machine clock, and one would have
    assumed midnight. A date-only value is worse than useless here because two
    runs on one day have to be orderable.
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def emit_json(data) -> None:
    """Print a payload, stamped with the time it was produced.

    The stamp is added here rather than in each command so that all fourteen
    carry it and none can forget. A caller that already set `checked_at` keeps
    its own value.
    """
    if isinstance(data, dict):
        data = dict(data)
        data.setdefault("checked_at", checked_at())
    print(json.dumps(data, indent=2, sort_keys=True, default=str, ensure_ascii=False))


def rule(title: str = "", width: int = 72) -> str:
    if not title:
        return "=" * width
    return "{} {}".format(title, "=" * max(0, width - len(title) - 1))


def kv(pairs: Dict[str, object], indent: int = 0) -> List[str]:
    if not pairs:
        return []
    pad = " " * indent
    width = max(len(str(k)) for k in pairs)
    lines = []
    for key, value in pairs.items():
        if value is None or value == "" or value == [] or value == {}:
            continue
        lines.append("{}{:<{w}}  {}".format(pad, str(key), value, w=width))
    return lines


def findings_text(findings: List[Dict[str, object]], counts: Optional[Dict[str, int]] = None) -> List[str]:
    """Findings as a person would want to read them: worst first, one per block."""
    lines: List[str] = []
    if counts:
        summary = ", ".join(
            "{} {}".format(counts.get(level, 0), level)
            for level in ("critical", "warning", "info")
            if counts.get(level)
        )
        lines.append(summary or "nothing flagged")
        lines.append("")
    if not findings:
        lines.append("No findings.")
        return lines
    for finding in findings:
        severity = str(finding.get("severity", "info"))
        lines.append(
            "{} {}  {}".format(
                SEVERITY_MARK.get(severity, "[ ]"), finding.get("check") or finding.get("rule"), ""
            ).rstrip()
        )
        lines.append("    {}".format(finding.get("message") or finding.get("note") or ""))
        for key in ("observed", "before", "after", "preview", "px", "chars", "examples"):
            if key in finding and finding[key] not in (None, "", [], {}):
                value = finding[key]
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value[:5])
                lines.append("    {}: {}".format(key, value))
        if finding.get("method"):
            lines.append("    method: {}".format(finding["method"]))
        lines.append("")
    return lines


def table(rows: List[Dict[str, object]], columns: List[str], limit: int = 25) -> List[str]:
    """A fixed-width table. Skills should read JSON; this is for a person."""
    if not rows:
        return ["(no rows)"]
    shown = rows[:limit]
    widths = {}
    for column in columns:
        widths[column] = max(
            len(column), *(len(_cell(row.get(column))) for row in shown)
        ) if shown else len(column)
    lines = ["  ".join(column.ljust(widths[column]) for column in columns)]
    lines.append("  ".join("-" * widths[column] for column in columns))
    for row in shown:
        lines.append("  ".join(_cell(row.get(column)).ljust(widths[column]) for column in columns))
    if len(rows) > limit:
        lines.append("... {} more rows, use --json for all of them".format(len(rows) - limit))
    return lines


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return "{:.4g}".format(value)
    text = str(value)
    return text if len(text) <= 60 else text[:57] + "..."
