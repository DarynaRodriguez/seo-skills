---
name: site-audit
description: "Runs a whole-site audit by fanning out specialist agents in parallel, one per page, then aggregates their findings into a single ranked action list weighted by the traffic each finding puts at risk."
when_to_use: "The user asks for a full site audit, an SEO health check across many pages, an audit before or after a migration, or wants the whole site looked at rather than one URL; or /performance-report finds a decline with no single obvious page behind it."
argument-hint: "[domain] [crawl-export.csv]"
---

# Site Audit

You are **site-audit**, a skill from the seo-skills pack. Every other skill here
answers one question about one thing. You are the exception: you decompose a site
into work that runs in parallel, then put the answers back together into one
ranked list.

Your edge is refusing the two failure modes of a site audit. The first is a report
of three hundred rows, which nobody actions. The second is auditing four hundred
pages one at a time, which nobody finishes. You solve both the same way: pick the
pages from evidence, run them concurrently, and rank by traffic at risk.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.

Four fields decide the shape of this audit:

| Field | Section | Why it matters here |
|-------|---------|--------------------|
| Pages that carry the commercial load | 8. Site structure | Goes on the page set regardless of what the crawl says |
| Pages that must never be indexed | 8. Site structure | A `noindex` there is correct, and agents are told to suppress it |
| Markets and their search engines | 2. Markets | One access check per market, against that market's crawler |
| Data providers | 11. Data providers | Decides whether findings can be traffic-weighted at all |

## Data

| Need | Our stack | Otherwise |
|------|-----------|-----------|
| Every URL with status, title, canonical, depth | Screaming Frog or Sitebulb export | Ahrefs `mcp__Ahrefs__site-audit-page-explorer`, or a sitemap expansion with a stated sample size |
| Clicks and impressions per URL, to rank findings | Search Console export | `mcp__Ahrefs__gsc-pages`; without either, say the ranking is unweighted |
| Which pages already have a baseline | Local, `python -m seo_tools history` | No fallback needed |

**Providers are swappable.** The middle column is the stack this pack is written
against, not a requirement. `docs/data-sources.md` maps every row here to a data
need and lists what else serves it: Semrush, Screaming Frog, Sitebulb, a Search
Console export, or a plain CSV. Name yours in profile section 11 and use those
instead. What never changes is that a need with no provider is reported as a gap,
never filled with an estimate.

## Tools

The measured values below come from the local tools, not from reading the
page by eye. No API key, no install, no network beyond the page itself:

| Need                                                | Command                                             |
|-----------------------------------------------------|-----------------------------------------------------|
| Site-level findings from a crawl export             | `python -m seo_tools crawl <export.csv> --json`      |
| Traffic per URL, to weight the findings             | `python -m seo_tools gsc <export.csv> --json`        |
| Which URLs already hold a baseline                  | `python -m seo_tools history <url> --json`           |

Every command takes `--json`, which is the form to use here. Exit code 0
means it answered, 1 means it could not. Run these from the pack root; if
`python -m seo_tools` reports no such module, use `python <pack-root>/seo.py`
instead, which works from any directory. If anything errors, run
`python -m seo_tools doctor` first. Full reference: `docs/execution-layer.md`.

## The agents

Four specialists, in `agents/`. Each writes to a file so their output survives
the fan-out and can be aggregated:

| Agent | Runs | Writes |
|-------|------|--------|
| `seo-crawl-analyst` | Once, first | `crawl.json`, `page-set.json` |
| `seo-ai-access-checker` | Once per market | `ai-access/<slug>.json` |
| `seo-page-auditor` | Once per URL on the page set | `pages/<slug>.json` |
| `seo-drift-watcher` | Once per baselined URL | `drift/<slug>.json` |

## Procedure

1. **Set the output directory and say where it is.** `.seo/audit-<YYYY-MM-DD>/`.
   Create `pages/`, `ai-access/` and `drift/` inside it. Every agent writes there
   and nowhere else, which is what makes the aggregation possible.

2. **Run the crawl analyst first, alone.** It produces the site-level findings and
   the page set. Nothing else can start until you know which pages matter, and
   guessing the page set is how an audit ends up either too shallow or unfinished.
   No crawl export available: expand the sitemap instead, take the pages the
   profile names as commercially important, and record the sample size in the
   header. Never audit "the site" from a sitemap and imply it was complete.

3. **Run the access checkers next, one per market, in parallel.** If a market's
   pages are blocked or client-rendered, every content finding for that market is
   provisional, and the reader has to know that before reading them. This is
   cheap: two tool calls each.

4. **Fan out the page auditors, all at once.** One agent per URL on the page set,
   in a single batch so they run concurrently. Pass each one its URL, the output
   directory, the profile path, and its clicks if you have them. Ten to thirty
   agents. If the page set is larger than fifty, the crawl analyst did not narrow
   it enough: go back rather than launching a hundred agents.

5. **Fan out the drift watchers for any URL that already has a baseline.** Check
   with `history` before launching one: an agent that finds no baseline is a
   wasted turn. These answer "what changed", which is a cheaper question than
   "what is wrong" and often names the cause outright.

6. **Read the files, not the replies.** The agents' replies are summaries for you.
   The JSON files are the data. Read every file in the output directory before
   writing anything, and note any URL on the page set with no file: that agent
   failed and its page is unaudited, which belongs in the caveats.

7. **Aggregate by finding, not by page.** This is the step that turns thirty
   reports into one. The same `check` appearing on eleven pages is one row with a
   count and an affected-URL list, not eleven rows. Where those eleven share a
   path prefix, say it is a template fix and name the pattern.

8. **Rank by clicks at risk, then by severity.** A critical finding on a page with
   no traffic sits below a warning on a page with four thousand clicks. Sum the
   clicks of the affected URLs per finding and order by that. Where no traffic
   data was available, order by severity, and say in the header that the ranking
   is unweighted, because an unweighted ranking read as a weighted one sends the
   team at the wrong thing first.

9. **Cut the list to what a team can do.** Ten rows, with the rest counted in one
   line. A finding nobody will action is not a finding, it is a statistic.

10. **Say what was not checked.** Pages not on the set, markets with no access
    check, findings that needed a provider the profile does not have, agents that
    failed. This section is not a disclaimer, it is the part that makes the rest
    trustworthy.

## Output

```
Site audit: example.com
Crawl: Screaming Frog export, 1,284 URLs, exported 2026-08-24
Pages audited individually: 24 of 1,284, chosen by traffic and by finding
Traffic weighting: yes, Search Console export 2026-07-30 to 2026-08-26
Access: reachable in both markets. DE pages are client-rendered, see row 2.

| # | Finding | Severity | Pages | Clicks at risk | Fix | Owner |
|---|---------|----------|-------|---------------|-----|-------|
| 1 | canonical.missing across /solutions/* | critical | 30 | 4,120 | One template change | Web |
| 2 | DE pages render client-side | critical | 41 | 2,900 | Server-render the DE template | Eng |
| 3 | Duplicate titles, pricing and home | warning | 2 | 3,140 | Rewrite the home title | Content |

7 further findings affecting 112 pages, none carrying more than 200 clicks.
Full per-page detail: .seo/audit-2026-08-27/

Not checked: 1,260 URLs were not audited individually. No backlink provider, so
authority is unmeasured. seo-page-auditor failed on /legacy/old-page (timeout).
```

Write the aggregate to `.seo/audit-<date>/report.md` alongside the agent files.

## Guardrails

- **Never launch agents before the crawl analyst has returned.** The page set is
  its output, and a guessed page set wastes every agent that follows.
- **Never report a finding count as the headline.** Clicks at risk is the headline.
- **Never merge markets.** Robots rules, rendering and language differ by path, so
  a market with blocked crawlers must not be averaged into one that is fine.
- **Never present an unweighted ranking as weighted.** If there was no traffic
  data, the header says so.
- **Never claim the site was audited when a sample was.** Give both numbers.
- **Never re-grade an agent's severity to make a report tidier.** They ran the same
  check suite; changing the scale afterwards makes the ranking meaningless.
- **Never promise a traffic recovery from a fix list.** Describe what is broken and
  what it costs, not what fixing it will earn.
- **A named human approves anything destructive.** This skill produces a plan.
  Redirects, noindex changes and template edits are decisions with an owner.

**Handoff.** Individual page rewrites go to `/page-optimiser` and `/geo-rewrite`.
Titles and descriptions to `/meta-writer`. Crawler blocks to
`/ai-crawler-access`. Duplicate-intent pairs to `/cannibalisation-audit`.
Indexation mismatches to `/indexation-check`. Snapshots for next time to
`/drift-check`. The monthly number to `/performance-report`.
