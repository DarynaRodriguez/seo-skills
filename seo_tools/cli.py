"""The command line surface. One entry point, one command per SEO question.

    python -m seo_tools <command> [args] [--json]

Skills call this with --json and read the result. A person runs it without and
reads the text. Every command exits 0 when it produced an answer, 1 when it
could not, and 2 on bad arguments, so a script can branch on it.
"""
from __future__ import annotations

import argparse
import sys
from urllib.parse import urlsplit
from typing import Dict, List, Optional

from . import (
    audits,
    crawl as crawl_module,
    drift as drift_rules,
    gsc as gsc_module,
    output,
    parsing,
    sitemaps,
    typography,
)
from .fetching import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, fetch, public_summary
from .robots import AI_AGENTS, RobotsTxt, robots_url_for
from .safety import UrlNotAllowed, normalise_url, redact, validate_url
from .store import Store, default_home

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2


def _fetch_or_die(url: str, args) -> Dict[str, object]:
    """Fetch, and turn an unreachable page into a clean failure rather than a traceback."""
    try:
        result = fetch(url, timeout=args.timeout, user_agent=args.user_agent)
    except UrlNotAllowed as exc:
        _fail("refused to fetch {}: {}".format(redact(url), exc), args)
    if not result.get("ok"):
        _fail("could not fetch {}: {}".format(redact(url), result.get("error")), args, result)
    return result


def _fail(message: str, args, payload: Optional[Dict[str, object]] = None) -> None:
    body = {"ok": False, "error": message}
    if payload:
        body.update({k: v for k, v in payload.items() if k != "body"})
        # The fetch result carries the URL as given, which may hold credentials.
        for key in ("url", "final_url"):
            if isinstance(body.get(key), str):
                body[key] = redact(body[key])
    if getattr(args, "json", False):
        output.emit_json(body)
    else:
        print("FAILED: {}".format(message), file=sys.stderr)
    raise SystemExit(EXIT_FAILED)


def _page_of(url: str, args) -> Dict[str, object]:
    result = _fetch_or_die(url, args)
    page = parsing.parse_page(str(result.get("text") or ""), str(result.get("final_url") or url))
    if not page.get("ok"):
        _fail(str(page.get("error")), args)
    page["status"] = result.get("status")
    page["_headers"] = {str(k).lower(): v for k, v in (result.get("headers") or {}).items()}
    page["_html"] = str(result.get("text") or "")
    page["_fetch"] = public_summary(result)
    return page


def _strip_private(page: Dict[str, object]) -> Dict[str, object]:
    return {k: v for k, v in page.items() if not k.startswith("_")}


# -- commands ------------------------------------------------------------


def cmd_fetch(args) -> int:
    result = _fetch_or_die(args.url, args)
    summary = public_summary(result)
    if args.json:
        output.emit_json(summary)
        return EXIT_OK
    print(output.rule("fetch"))
    print("\n".join(output.kv({
        "requested": summary["url"],
        "final": summary["final_url"],
        "status": summary["status"],
        "redirects": summary["redirect_count"],
        "bytes": summary["bytes"],
        "encoding": "{} (from {})".format(summary["encoding"], summary["encoding_source"]),
        "time": "{} ms".format(summary["elapsed_ms"]),
    })))
    if summary["redirect_count"]:
        print("\n" + output.rule("redirect chain"))
        for hop in summary["redirect_chain"]:
            arrow = " -> {}".format(hop["location"]) if hop.get("location") else ""
            print("  {} {}{}".format(hop["status"], hop["url"], arrow))
    if summary["headers"]:
        print("\n" + output.rule("headers"))
        print("\n".join(output.kv(summary["headers"], indent=2)))
    return EXIT_OK


def cmd_page(args) -> int:
    page = _page_of(args.url, args)
    result = audits.audit_page(page, page.get("_headers"))
    payload = {
        "page": _strip_private(page),
        "fetch": page["_fetch"],
        "findings": result["findings"],
        "counts": result["counts"],
    }
    if args.json:
        output.emit_json(payload)
        return EXIT_OK
    print(output.rule("page"))
    print("\n".join(output.kv({
        "url": page.get("url"),
        "status": page.get("status"),
        "title": page.get("title"),
        "description": page.get("meta_description"),
        "canonical": page.get("canonical"),
        "robots": page.get("meta_robots"),
        "lang": page.get("html_lang"),
        "h1": " | ".join(page.get("h1") or []),
        "words (main)": page.get("main_word_count"),
        "words (all)": page.get("word_count"),
        "schema": ", ".join(page.get("schema_types") or []) or None,
        "images": "{} ({} without alt)".format(page.get("images"), page.get("images_missing_alt")),
        "links": "{} internal, {} external".format(page.get("links_internal"), page.get("links_external")),
        "needs JS": page.get("requires_js"),
    })))
    print("\n" + output.rule("findings"))
    print("\n".join(output.findings_text(result["findings"], result["counts"])))
    return EXIT_OK if not result["counts"].get("critical") else EXIT_FAILED


def cmd_meta(args) -> int:
    if args.url:
        page = _page_of(args.url, args)
        title = page.get("title") or ""
        description = page.get("meta_description") or ""
        source = page.get("url")
    else:
        title = args.title or ""
        description = args.description or ""
        source = "supplied on the command line"
        page = {"title": title, "meta_description": description, "h1": []}

    payload = {
        "source": source,
        "title": typography.measure_title(str(title)) if title else None,
        "description": typography.measure_description(str(description)) if description else None,
        "findings": audits.check_meta(page),
    }
    if args.json:
        output.emit_json(payload)
        return EXIT_OK
    print(output.rule("meta"))
    for label, measured in (("title", payload["title"]), ("description", payload["description"])):
        if not measured:
            print("{}: missing".format(label))
            continue
        print("{}: {}".format(label, measured["text"]))
        print("  {} chars, an estimated {} px of {} px ({}% of the budget){}".format(
            measured["chars"], measured["px"], measured["px_limit"], measured["px_used_pct"],
            ", truncates" if measured["truncates"] else "",
        ))
        if measured["truncates"]:
            print("  shows as: {}".format(measured["truncated_preview"]))
    print("\n" + output.rule("findings"))
    print("\n".join(output.findings_text(payload["findings"])))
    # The method depends on the script, so read it off the measurement rather
    # than printing the Latin default at a CJK title.
    for measured in (payload["title"], payload["description"]):
        if measured:
            print(measured["method"])
            break
    return EXIT_OK


def cmd_headings(args) -> int:
    page = _page_of(args.url, args)
    findings = audits.check_headings(page)
    if args.json:
        output.emit_json({"url": page.get("url"), "headings": page.get("headings"), "findings": findings})
        return EXIT_OK
    print(output.rule("outline"))
    for heading in page.get("headings") or []:
        print("{}{} {}".format("  " * (int(heading["level"]) - 1), "H" + str(heading["level"]), heading["text"]))
    print("\n" + output.rule("findings"))
    print("\n".join(output.findings_text(findings)))
    return EXIT_OK


def cmd_schema(args) -> int:
    page = _page_of(args.url, args)
    findings = audits.check_schema(page)
    payload = {
        "url": page.get("url"),
        "types": page.get("schema_types"),
        "blocks": page.get("schema_blocks"),
        "findings": findings,
    }
    if args.json:
        output.emit_json(payload)
        return EXIT_OK
    print(output.rule("structured data"))
    print("types: {}".format(", ".join(page.get("schema_types") or []) or "none"))
    print("blocks: {}".format(len(page.get("schema_blocks") or [])))
    print("\n" + output.rule("findings"))
    print("\n".join(output.findings_text(findings)))
    return EXIT_OK


def cmd_robots(args) -> int:
    # Validate what the user typed, not what robots_url_for derives from it:
    # that helper keeps only the scheme and host, so it silently drops
    # credentials and would accept a URL every other command refuses.
    validate_url(args.url)
    robots_url = robots_url_for(args.url)
    result = fetch(robots_url, timeout=args.timeout, user_agent=args.user_agent)
    if not result.get("ok"):
        _fail("could not fetch {}: {}".format(robots_url, result.get("error")), args)
    parsed = RobotsTxt(
        str(result.get("text") or ""), int(result.get("status") or 200), url=str(result.get("final_url"))
    )
    if args.agent:
        verdict = parsed.can_fetch(args.agent, args.url)
        payload = {"robots_txt": robots_url, "agent": args.agent, "url": args.url, **verdict}
        if args.json:
            output.emit_json(payload)
            return EXIT_OK
        print("{}: {}".format(args.agent, "allowed" if verdict["allowed"] else "BLOCKED"))
        print(verdict["reason"])
        return EXIT_OK if verdict["allowed"] else EXIT_FAILED

    audit = parsed.audit_ai_agents(args.url)
    audit["robots_txt"] = robots_url
    if args.json:
        output.emit_json(audit)
        return EXIT_OK

    print(output.rule("robots.txt"))
    print("\n".join(output.kv({
        "file": robots_url,
        "status": audit["robots_status"],
        "groups": len(parsed.groups),
        "sitemaps": len(parsed.sitemaps),
    })))
    print("\n" + output.rule("AI and search crawlers"))
    print("\n".join(output.table(
        audit["agents"],
        ["agent", "operator", "purpose", "allowed", "matched_rule"],
        limit=len(audit["agents"]),
    )))
    if audit["blocked_search_index"] or audit["blocked_live_fetch"]:
        print("\n" + output.rule("costs you citations"))
        for agent in audit["blocked_search_index"] + audit["blocked_live_fetch"]:
            print("  {}: {}".format(agent, AI_AGENTS[agent]["cost_of_blocking"]))
    if audit["blocked_training"]:
        print("\n" + output.rule("training only, no citation effect"))
        print("  " + ", ".join(audit["blocked_training"]))
    if parsed.unknown_directives:
        print("\n" + output.rule("lines that apply to nobody"))
        for line in parsed.unknown_directives[:10]:
            print("  {}".format(line))
    return EXIT_OK


def cmd_sitemap(args) -> int:
    validate_url(args.url)
    discovery = sitemaps.discover(args.url)
    expanded = sitemaps.expand(discovery, limit=args.limit) if args.expand else None
    payload = {"discovery": discovery, "expanded": expanded}
    if args.json:
        output.emit_json(payload)
        return EXIT_OK
    print(output.rule("sitemaps"))
    print("\n".join(output.kv({
        "site": discovery["site"],
        "robots.txt reachable": discovery["robots_reachable"],
        "declared in robots": len(discovery["declared_in_robots"]),
        "reachable": discovery["reachable_count"],
        "urls in flat sitemaps": discovery["total_urls"],
    })))
    if discovery["stale_declarations"]:
        print("\ndeclared in robots.txt but unreachable:")
        for url in discovery["stale_declarations"]:
            print("  {}".format(url))
    print("\n" + output.rule("found"))
    print("\n".join(output.table(
        [s for s in discovery["sitemaps"] if s.get("reachable")],
        ["url", "kind", "count", "declared_in_robots"],
    )))
    if expanded:
        print("\n" + output.rule("expanded"))
        print("\n".join(output.kv({
            "child sitemaps": len(expanded["child_sitemaps"]),
            "unique urls": expanded["url_count"],
            "duplicates": expanded["duplicates"],
            "lastmod coverage": "{}%".format(expanded["lastmod_coverage_pct"]),
            "truncated at": expanded["truncated_at"],
        })))
    return EXIT_OK


def cmd_baseline(args) -> int:
    page = _page_of(args.url, args)
    with Store(args.home) as store:
        saved = store.save_baseline(args.url, page, page["_html"], label=args.label)
    if args.json:
        output.emit_json(saved)
        return EXIT_OK
    print(output.rule("baseline saved"))
    print("\n".join(output.kv(saved)))
    return EXIT_OK


def cmd_drift(args) -> int:
    with Store(args.home) as store:
        baseline = (
            store.baseline_by_id(args.baseline_id) if args.baseline_id else store.latest_baseline(args.url)
        )
        if not baseline:
            _fail(
                "no baseline for {} in {}. Run: python -m seo_tools baseline {}".format(
                    normalise_url(args.url), store.path, args.url
                ),
                args,
            )
        page = _page_of(args.url, args)
        result = drift_rules.compare(baseline, page)
        comparison_id = store.save_comparison(args.url, int(baseline["baseline_id"]), result)
    result["comparison_id"] = comparison_id
    if args.json:
        output.emit_json(result)
        return EXIT_OK
    print(output.rule("drift"))
    print("\n".join(output.kv({
        "url": result["url"],
        "baseline": "#{} captured {}".format(result["baseline_id"], result["baseline_captured_at"]),
        "verdict": result["verdict"],
    })))
    print("\n" + output.rule("changes"))
    print("\n".join(output.findings_text(result["changes"], result["counts"])))
    return EXIT_OK if not result["counts"].get("critical") else EXIT_FAILED


def cmd_history(args) -> int:
    with Store(args.home) as store:
        payload = store.history(args.url, limit=args.limit)
    if args.json:
        output.emit_json(payload)
        return EXIT_OK
    print(output.rule("history"))
    print("database: {}".format(payload["database"]))
    print("\nbaselines:")
    print("\n".join(output.table(
        payload["baselines"], ["baseline_id", "captured_at", "label", "status", "html_hash"]
    )))
    print("\ncomparisons:")
    print("\n".join(output.table(
        payload["comparisons"], ["id", "compared_at", "baseline_id", "critical", "warning", "info"]
    )))
    return EXIT_OK


def cmd_gsc(args) -> int:
    try:
        current = gsc_module.load_csv(args.csv, columns=args.columns)
        previous = (
            gsc_module.load_csv(args.compare, columns=args.columns) if args.compare else None
        )
    except gsc_module.GscError as exc:
        _fail(str(exc), args)

    rows = current["rows"]
    payload: Dict[str, object] = {
        "file": current["path"],
        "columns_detected": current["columns_detected"],
        "columns_resolved_by": current["columns_resolved_by"],
        "columns_ignored": current["columns_ignored"],
        "rows": current["row_count"],
        "totals": gsc_module.summarise(rows),
        "striking_distance": gsc_module.striking_distance(rows, min_impressions=args.min_impressions),
        "ctr_outliers": gsc_module.ctr_outliers(rows, min_impressions=args.min_impressions),
        "cannibalisation": gsc_module.cannibalisation(rows, min_impressions=args.min_impressions),
    }
    if previous:
        payload["comparison"] = gsc_module.compare_periods(
            rows, previous["rows"], dimension=args.dimension, min_impressions=args.min_impressions
        )
        payload["compared_with"] = previous["path"]

    if args.json:
        output.emit_json(payload)
        return EXIT_OK

    print(output.rule("search console export"))
    print("\n".join(output.kv({
        "file": current["path"],
        "rows": current["row_count"],
        "columns": ", ".join(current["columns_detected"]),
        "ignored": ", ".join(current["columns_ignored"]) or None,
    })))
    print("\n" + output.rule("totals"))
    print("\n".join(output.kv(payload["totals"])))

    striking = payload["striking_distance"]
    print("\n" + output.rule("positions 8 to 20 with impressions to convert"))
    print("\n".join(output.table(striking, ["query", "page", "position", "impressions", "clicks", "ctr"])))

    outliers = payload["ctr_outliers"]
    print("\n" + output.rule("CTR below the median for its position band"))
    print("benchmark: {}".format(outliers["benchmark"]))
    print("\n".join(output.table(
        outliers["findings"], ["query", "page", "position", "impressions", "ctr", "band_median_ctr", "shortfall_pct"]
    )))

    cannib = payload["cannibalisation"]
    print("\n" + output.rule("more than one URL on the same query"))
    if not cannib["supported"]:
        print(cannib["note"])
    else:
        print("{} queries with competing pages".format(cannib["group_count"]))
        for group in cannib["groups"][:10]:
            print("\n  {!r}  {} impressions across {} pages".format(
                group["query"], group["total_impressions"], group["pages_competing"]
            ))
            for entry in group["pages"]:
                print("    {:>6} impr  {:>4} clicks  pos {:<5}  {}".format(
                    entry["impressions"], entry["clicks"], entry["avg_position"], entry["page"]
                ))

    if previous:
        comparison = payload["comparison"]
        print("\n" + output.rule("period on period"))
        if not comparison["supported"]:
            print(comparison["note"])
        else:
            print(comparison["caveat"])
            print("\nbefore: {}".format(comparison["totals_before"]))
            print("now:    {}".format(comparison["totals_now"]))
            print("\nbiggest losses:")
            print("\n".join(output.table(
                comparison["biggest_losses"],
                [args.dimension, "clicks_before", "clicks_now", "clicks_delta", "position_before", "position_now"],
            )))
    return EXIT_OK



def cmd_crawl(args) -> int:
    """Read a crawl export from any tool and report what it can answer alone."""
    try:
        loaded = crawl_module.load_crawl(args.csv, columns=args.columns)
    except crawl_module.CrawlError as exc:
        _fail(str(exc), args)

    rows = loaded["rows"]
    result = crawl_module.analyse(rows, thin_threshold=args.thin)
    payload = {
        "file": loaded["path"],
        "exporter": loaded["exporter"],
        "columns_detected": loaded["columns_detected"],
        "columns_ignored": loaded["columns_ignored"],
        "columns_resolved_by": loaded["columns_resolved_by"],
        "rows": loaded["row_count"],
    }
    payload.update(result)

    if args.json:
        output.emit_json(payload)
        return EXIT_OK

    newline = "\n"
    summary = result["summary"]
    print(output.rule("crawl export"))
    print(newline.join(output.kv({
        "file": loaded["path"],
        "exporter": loaded["exporter"],
        "urls": summary["urls"],
        "columns": ", ".join(loaded["columns_detected"]),
        "resolved by": loaded["columns_resolved_by"],
    })))

    print(newline + output.rule("shape of the crawl"))
    print(newline.join(output.kv({
        "by status": ", ".join(
            "{} {}".format(count, band) for band, count in summary["by_status_band"].items()
        ),
        "indexable": summary["indexable"],
        "not indexable": summary["non_indexable"],
        "indexability unknown": summary["indexability_unknown"],
        "max crawl depth": summary["max_crawl_depth"],
        "median crawl depth": summary["median_crawl_depth"],
    })))

    sections = (
        ("could not be fetched", result["broken"], ["url", "status", "inlinks"]),
        (
            "redirect chains",
            result["redirect_chains"],
            ["url", "status", "redirects_to", "then_status"],
        ),
        ("canonical points elsewhere", result["non_self_canonical"], ["url", "canonical", "status"]),
        (
            "thin pages under {} words".format(result["thin_threshold"]),
            result["thin"],
            ["url", "word_count", "crawl_depth"],
        ),
    )
    for title, entries, columns in sections:
        print(newline + output.rule(title))
        print("{} found".format(len(entries)))
        if entries:
            print(newline.join(output.table(entries, columns, limit=15)))

    for label, key in (
        ("titles", "duplicate_titles"),
        ("descriptions", "duplicate_descriptions"),
        ("H1s", "duplicate_h1"),
    ):
        groups = result[key]
        print(newline + output.rule("duplicate {}".format(label)))
        print(
            "{} groups covering {} URLs".format(
                len(groups), sum(group["count"] for group in groups)
            )
        )
        for group in groups[:5]:
            print("  {}x  {}".format(group["count"], str(group["value"])[:70]))
            for url in group["urls"][:3]:
                print("        {}".format(url))

    print(newline + output.rule("missing on indexable pages"))
    print(newline.join(output.kv({
        "no title": len(result["missing_titles"]),
        "no meta description": len(result["missing_descriptions"]),
        "no H1": len(result["missing_h1"]),
        "no inlinks (orphans)": len(result["orphans"]),
    })))
    print(newline + "Use --json for the full lists.")
    return EXIT_OK



def cmd_normalise(args) -> int:
    """Canonical form of a URL, for joining two datasets that disagree about it.

    Exists as a command because the alternative was telling callers to run
    `python -c "from seo_tools.safety import normalise_url; ..."`, which fails
    everywhere except the pack root: the same defect the launcher exists to fix.
    An agent joining a crawl to a Search Console export needs this and should not
    have to reach into the package to get it.
    """
    rows = []
    for url in args.urls:
        try:
            key = normalise_url(url)
        except ValueError as exc:
            rows.append({"url": url, "normalised": None, "ok": False, "error": str(exc)})
            continue
        # normalise_url is a key generator, not a validator, so it happily returns
        # something for a string that is not a URL at all. Say so: a caller
        # computing a join match rate needs to know the input was junk rather than
        # counting it as a key that simply did not match.
        parts = urlsplit(key)
        if not parts.scheme or not parts.netloc:
            rows.append({
                "url": url,
                "normalised": key,
                "ok": False,
                "error": "not a URL: no scheme or host, so this is not a usable join key",
            })
            continue
        rows.append({"url": url, "normalised": key, "ok": True})

    # One exit code for both output modes. The JSON caller is the one most likely
    # to be a script testing the status rather than reading the rows, so having
    # --json always succeed is exactly backwards.
    code = EXIT_OK if all(r["ok"] for r in rows) else EXIT_FAILED

    if args.json:
        output.emit_json({"count": len(rows), "urls": rows})
        return code
    for row in rows:
        if row["ok"]:
            print(row["normalised"])
        else:
            print("could not normalise {}: {}".format(row["url"], row["error"]), file=sys.stderr)
    return code


def cmd_doctor(args) -> int:
    """Answer "will this work on my machine" before anyone runs a real command."""
    import platform
    import sqlite3

    checks: List[Dict[str, object]] = []

    version_ok = sys.version_info >= (3, 9)
    checks.append({
        "check": "python",
        "ok": version_ok,
        "detail": "{} on {}".format(platform.python_version(), platform.platform()),
        "fix": None if version_ok else "seo-skills needs Python 3.9 or newer.",
    })
    checks.append({"check": "sqlite3", "ok": True, "detail": sqlite3.sqlite_version, "fix": None})

    try:
        home = default_home()
        home.mkdir(parents=True, exist_ok=True)
        probe = home / ".write-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        checks.append({"check": "storage", "ok": True, "detail": str(home), "fix": None})
    except OSError as exc:
        checks.append({
            "check": "storage", "ok": False, "detail": str(exc),
            "fix": "Set SEO_SKILLS_HOME to a directory you can write to.",
        })

    if args.offline:
        checks.append({"check": "network", "ok": True, "detail": "skipped (--offline)", "fix": None})
    else:
        probe_url = "https://example.com/"
        result = fetch(probe_url, timeout=10)
        checks.append({
            "check": "network",
            "ok": bool(result.get("ok")),
            "detail": "{} -> {}".format(probe_url, result.get("status") or result.get("error")),
            "fix": None if result.get("ok") else "No outbound HTTPS. Check a proxy or firewall.",
        })

    encoding = (sys.stdout.encoding or "").lower()
    utf8 = "utf" in encoding
    checks.append({
        "check": "stdout encoding", "ok": utf8, "detail": sys.stdout.encoding,
        "fix": None if utf8 else "Set PYTHONIOENCODING=utf-8 so output does not mangle.",
    })

    ok = all(c["ok"] for c in checks)
    if args.json:
        output.emit_json({"ok": ok, "checks": checks})
        return EXIT_OK if ok else EXIT_FAILED
    print(output.rule("doctor"))
    for check in checks:
        print("{} {:<16} {}".format("ok  " if check["ok"] else "FAIL", check["check"], check["detail"]))
        if check["fix"]:
            print("     fix: {}".format(check["fix"]))
    print("\n{}".format("Everything needed is present." if ok else "Something above needs fixing."))
    return EXIT_OK if ok else EXIT_FAILED


# -- wiring --------------------------------------------------------------


def _common_flags() -> argparse.ArgumentParser:
    """Flags every command accepts, attached to each subparser as well as the root.

    Without this, `... page URL --json` is a usage error and only
    `... --json page URL` works. The first form is the one everybody writes,
    including the skills, so both have to work.
    """
    common = argparse.ArgumentParser(add_help=False)
    # SUPPRESS rather than a real default: the root parser and the subparser
    # share these dests, so a concrete default on the subparser would overwrite
    # a value the user passed before the command name. With SUPPRESS the
    # attribute appears only when someone actually set it, and _apply_defaults
    # fills in the rest.
    common.add_argument(
        "--json", action="store_true", default=argparse.SUPPRESS, help="machine-readable output"
    )
    common.add_argument(
        "--timeout", type=float, default=argparse.SUPPRESS, help="seconds per request"
    )
    common.add_argument("--user-agent", default=argparse.SUPPRESS, help="User-Agent to send")
    common.add_argument(
        "--home", default=argparse.SUPPRESS, help="directory for the baseline database"
    )
    return common


COMMON_DEFAULTS = {
    "json": False,
    "timeout": DEFAULT_TIMEOUT,
    "user_agent": DEFAULT_USER_AGENT,
    "home": None,
}


def _apply_defaults(args: argparse.Namespace) -> argparse.Namespace:
    for name, value in COMMON_DEFAULTS.items():
        if not hasattr(args, name):
            setattr(args, name, value)
    return args


def build_parser() -> argparse.ArgumentParser:
    common = _common_flags()
    parser = argparse.ArgumentParser(
        prog="python -m seo_tools",
        parents=[common],
        description="Deterministic SEO measurements for the seo-skills pack. "
        "Standard library only, no install step, no API keys.",
        epilog="Every command takes --json, which is how the skills call it. "
        "The flag works before or after the command name.",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    def add(name: str, handler, help_text: str):
        child = sub.add_parser(name, help=help_text, description=help_text, parents=[common])
        child.set_defaults(handler=handler)
        return child

    add("fetch", cmd_fetch, "Fetch a URL and show the status, redirect chain and SEO headers.").add_argument("url")
    add("page", cmd_page, "Full on-page extraction and audit of one URL.").add_argument("url")

    meta = add("meta", cmd_meta, "Measure a title and description in pixels, not characters.")
    meta.add_argument("url", nargs="?", help="URL to read them from")
    meta.add_argument("--title", help="measure this title instead of fetching")
    meta.add_argument("--description", help="measure this description instead of fetching")

    add("headings", cmd_headings, "Show the heading outline and flag breaks in it.").add_argument("url")
    add("schema", cmd_schema, "Validate JSON-LD structured data on a page.").add_argument("url")

    robots = add("robots", cmd_robots, "Evaluate robots.txt against the AI and search crawlers that matter.")
    robots.add_argument("url")
    robots.add_argument("--agent", help="test one user-agent instead of the whole table")

    sitemap = add("sitemap", cmd_sitemap, "Discover and parse the sitemaps for a site.")
    sitemap.add_argument("url")
    sitemap.add_argument("--expand", action="store_true", help="walk a sitemap index one level down")
    sitemap.add_argument("--limit", type=int, default=5000, help="stop after this many URLs")

    baseline = add("baseline", cmd_baseline, "Store the current state of a page as a known good snapshot.")
    baseline.add_argument("url")
    baseline.add_argument("--label", help="a note to remember why this snapshot was taken")

    drift = add("drift", cmd_drift, "Compare a page against its stored baseline.")
    drift.add_argument("url")
    drift.add_argument("--baseline-id", type=int, help="compare against a specific snapshot")

    history = add("history", cmd_history, "List the baselines and comparisons held for a URL.")
    history.add_argument("url")
    history.add_argument("--limit", type=int, default=20)

    crawl = add(
        "crawl",
        cmd_crawl,
        "Analyse a crawl export from Screaming Frog, Sitebulb or any CSV. No API needed.",
    )
    crawl.add_argument("csv", help="the crawl export to read")
    crawl.add_argument("--thin", type=int, default=300, help="word count below which a page is listed as thin")
    crawl.add_argument(
        "--columns",
        help="name the columns positionally when the headers are not recognised, "
        "e.g. url,status,title,meta_description. Use - to skip one",
    )

    gsc = add("gsc", cmd_gsc, "Analyse a Search Console CSV export. No API access needed.")
    gsc.add_argument("csv", help="the export to analyse")
    gsc.add_argument("--compare", help="an earlier export, to diff period on period")
    gsc.add_argument("--dimension", choices=("page", "query"), default="page", help="what to join on")
    gsc.add_argument("--min-impressions", type=float, default=100, help="ignore rows below this")
    gsc.add_argument(
        "--columns",
        help="name the columns positionally when the export is in a language the "
        "aliases do not cover, e.g. query,clicks,impressions,ctr,position. Use - to skip one",
    )

    normalise = add(
        "normalise",
        cmd_normalise,
        "Print the canonical form of one or more URLs, for joining datasets that "
        "disagree about trailing slashes, www, casing or tracking parameters.",
    )
    normalise.add_argument("urls", nargs="+", help="one or more URLs")

    doctor = add("doctor", cmd_doctor, "Check this machine can run the tools.")
    doctor.add_argument("--offline", action="store_true", help="skip the network check")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = _apply_defaults(parser.parse_args(argv))
    if not getattr(args, "command", None):
        parser.print_help()
        return EXIT_USAGE
    if args.command == "meta" and not args.url and not (args.title or args.description):
        parser.error("meta needs a URL, or --title and --description")
    try:
        return int(args.handler(args))
    except UrlNotAllowed as exc:
        # Commands that fetch through a helper already catch this. Commands that
        # call fetch directly, robots and sitemap among them, did not, and
        # printed a traceback at a user who mistyped a scheme. Caught here so it
        # cannot happen again in a command added later.
        _fail("refused to fetch: {}".format(exc), args)
    except UnicodeEncodeError:
        print(
            "Output could not be encoded. Set PYTHONIOENCODING=utf-8 and run again.",
            file=sys.stderr,
        )
        return EXIT_FAILED
    except KeyboardInterrupt:
        return EXIT_FAILED
