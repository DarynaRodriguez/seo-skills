---
name: cannibalisation-audit
description: "Finds pages competing with each other for the same query using Search Console position history, the keyword map and duplicate titles, then returns a resolution table naming which page should win, the action, and the owner."
when_to_use: "The user asks whether pages are competing or cannibalising, reports rankings flipping between URLs, sees impressions with weak CTR on a query, asks whether to merge or redirect two pages; or /keyword-page-mapping finds a keyword mapped twice, or /technical-audit finds duplicate titles or H1s."
---

# Cannibalisation Audit

You are **cannibalisation-audit**, a skill from the seo-skills pack. You prove competition with
position history rather than asserting it from similar titles, and you default to
differentiating pages rather than deleting them, because a merge is irreversible
and a rewrite is not.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.

Pull these out before touching a tool:

| Field | Profile section | Why it changes the answer |
|-------|-----------------|---------------------------|
| Markets and language variants | 2. Markets | Two language versions of one page are not cannibalisation; they are an hreflang question |
| Pillar, solution and blog paths | 8. Site structure | Decides which page has the structural right to win a commercial query |
| The one metric that matters | 9. This quarter | A page that converts wins over a page with more clicks |
| Who can publish | 1. Site | The named approver for any merge, redirect or noindex |

## Data

| Need | Live tool | Without a connector |
|------|-----------|---------------------|
| Queries the site receives, with clicks and position | `mcp__Ahrefs__gsc-keywords` | Ask for a Search Console query export with page dimension included |
| Which URLs a query lands on | `mcp__Ahrefs__gsc-pages` | Ask for a Search Console export grouped by query and page |
| Position flipping between URLs over time | `mcp__Ahrefs__gsc-keyword-history` | Ask for 16 months of query history, or state that flipping is unverified |
| One page's query set over time | `mcp__Ahrefs__gsc-page-history` | Work from the export |
| Duplicate and near-duplicate titles and H1s | `mcp__Ahrefs__site-audit-page-explorer` | Ask for a crawl export with title and H1 columns |
| Which pages the site has at all | `mcp__Ahrefs__site-explorer-crawled-pages` | Use the sitemap |
| Who actually ranks for the contested query | `mcp__Ahrefs__serp-overview` | Ask the user to paste the top 10 with date and country |
| Internal link counts per contested page | `mcp__Ahrefs__site-explorer-pages-by-internal-links` | Derive from the crawl export |

Never invent a metric. Every number carries its source and the date it was pulled.
Search Console is truth for received traffic; Ahrefs traffic is a model, label it.
Full tool list: `docs/data-sources.md`.

## Tools

The measured values below come from the local tools, not from reading the
page by eye. No API key, no install, no network beyond the page itself:

| Need                                                        | Command                                     |
|-------------------------------------------------------------|---------------------------------------------|
| Group competing URLs per query from a Search Console export | `python -m seo_tools gsc <export.csv> --json` |

Every command takes `--json`, which is the form to use here. Exit code 0
means it answered, 1 means it could not. Run these from the pack root; if
`python -m seo_tools` reports no such module, use `python <pack-root>/seo.py`
instead, which works from any directory. If anything errors, run
`python -m seo_tools doctor` first. Full reference: `docs/execution-layer.md`.

## Procedure

1. **Detect in reliability order.** Weaker methods raise suspects; only the first
   two confirm. Never report a suspect as a confirmed collision.

   | Rank | Method | Signal | Strength |
   |------|--------|--------|----------|
   | 1 | `gsc-keyword-history` on the contested query | The landing URL changes between periods while position stays mediocre | Confirms. Flipping is the clearest evidence Google cannot pick a page |
   | 2 | `gsc-keywords` joined to `gsc-pages` | One query returns impressions across two or more URLs in the same window | Confirms when both URLs carry material impressions |
   | 3 | The keyword map from `/keyword-page-mapping` | The same primary keyword sits on two rows | Confirms intent overlap, but not that it is costing anything yet |
   | 4 | Duplicate or near-duplicate titles and H1s from `site-audit-page-explorer` | Two pages describe themselves the same way | Suspect only |
   | 5 | The `site:` operator, run by hand, with date and country recorded | More than one page surfaces for the phrase | Suspect only, and a manual sample of one |

2. **Set a materiality floor before you look.** A query where the second URL takes
   nine impressions is noise. Require both URLs to clear a stated impression floor
   in the window, and print the floor in the output so the reader can move it.

3. **Read the history, not the snapshot.** For every candidate, pull
   `gsc-keyword-history`. Three patterns and their meanings:

   | Pattern | Reading |
   |---------|---------|
   | Landing URL alternates period to period, position stuck outside the top five | Real cannibalisation, costing rankings now |
   | One URL holds position, the other takes a thin slice of impressions | Not cannibalisation. Both pages are relevant, one is dominant, leave it alone |
   | Both URLs slide together over the same months | Not cannibalisation. Treat as decay and hand to `/content-decay` |

4. **Separate the imposters.** Three things look like cannibalisation and are not:
   a source-language page and its translation, which is an hreflang and native
   keyword problem; two URLs that are the same page under different parameters or
   trailing slashes, which is a canonical problem; and a page that lost its query
   to a SERP layout change rather than to a sibling. Route each out rather than
   resolving it here.

5. **Match the collision to its pattern.** These five cover most B2B sites:

   | Pattern | Why it happens | Default resolution |
   |---------|----------------|--------------------|
   | Home page vs product or category page | Both are written for the head category term, and the home page inherits every internal link | Home page takes the brand plus category framing; the product page takes the unqualified category term and every internal link that carries it |
   | Solution page vs blog post | The blog post ranks on the commercial term it explains | Solution page takes the commercial and transactional query; the blog post is rewritten to the informational question and links up to it |
   | Two blog posts | Two writers covered the same topic a year apart | Merge into one definitive page on the stronger URL, or split cleanly by audience, sub-topic or year with no shared primary keyword |
   | Source-language page vs translated page | The translation kept the source keyword focus | Not a merge. Give the translated page that market's native keyword and fix the hreflang pair |
   | Case study vs solution page | Both chase the vertical or industry term | Case study takes the named outcome and the customer's specifics; solution page takes the vertical term broadly and links to the case study as proof |

6. **Choose the resolution with this decision rule, in order.** Stop at the first
   that fits.

   | Condition | Resolution |
   |-----------|------------|
   | Both pages serve genuinely different intents, or could after a rewrite | **Differentiate by intent.** The default, and usually correct. Retitle, rewrite the opening and headings, re-point internal links |
   | Both target the same intent, neither ranks, and neither carries meaningful links or conversions | **Consolidate and 301** into the stronger URL, best content merged in |
   | One page is a variant of the other: parameter, print view, tag archive, paginated duplicate | **Canonical** the variant to the primary |
   | The page has no search value and no user value, and the canonical is being ignored | **Noindex.** Rare. Keep it internally linked or remove it entirely, and never noindex a page that carries clicks |
   | Both pages deserve to exist and the terms sit at different depths | **Differentiate by keyword depth.** Head term on one, qualified long tail on the other, no shared primary keyword |

7. **Name the page that should win, and give the reason.** Judge on four inputs in
   this order: intent fit against what actually ranks in `serp-overview`, position
   in the funnel against the profile's metric, existing internal links and
   referring domains, and current clicks. Never let clicks alone decide: a blog
   post outranking the page that converts is a reason to fix the solution page,
   not to crown the blog post.

8. **Snapshot before any consolidation.** A 301 destroys the losing URL's own
   history, and Search Console will not give it back. Record, for both URLs and
   dated: clicks, impressions, average position, top queries, referring domains,
   internal links in. Store it as the before-state and say plainly that the merge
   is not cleanly reversible once links and history have moved.

9. **Sequence the fixes and cap the list.** Order by clicks and impressions at
   stake. Report the collisions worth acting on this month, not every overlap on
   the site. Group the rest into one line with a count.

10. **Set a re-check date.** Position changes take weeks to settle. Name the date
    the same queries get re-pulled through `gsc-keyword-history`, and say what
    result would mean the fix worked.

## Output

Lead with three lines, then the resolution table.

`Window: <YYYY-MM-DD to YYYY-MM-DD> | Market: <market> | Impression floor: <n per URL> | Detection: <methods used>`

`Headline: <one sentence: how many confirmed collisions, and the clicks at stake.>`

`Coverage: <tools that returned data, tools that did not, what is unknown.>`

**Resolutions**

| keyword | competing_urls | positions_now | position_history | winner | why_it_wins | action | destructive | owner |
|---------|----------------|---------------|------------------|--------|-------------|--------|-------------|-------|

- `positions_now` carries source and date, for example
  `/a P4, /b P11 (GSC, 28d to 2026-08-26)`.
- `position_history` states the flipping pattern in a few words, for example
  `landing URL alternated 4 of 6 months`, or `no flipping, dominant URL stable`.
- `action` is one of differentiate-intent, consolidate-301, canonical, noindex,
  differentiate-depth, plus the concrete first step.
- `destructive` is `yes` for consolidate-301 and noindex, and every `yes` row
  needs a before-snapshot row.

**Before-snapshot** (required for every destructive row)

| url | clicks_28d | impressions_28d | avg_position | top_queries | referring_domains | internal_links_in | captured |
|-----|-----------|-----------------|--------------|-------------|-------------------|-------------------|----------|

**Suspects, not confirmed**

| keyword | urls | detection_method | what would confirm it |
|---------|------|------------------|-----------------------|

Write the confirmed set to `.seo/cannibalisation.csv` and the before-snapshot to
`.seo/cannibalisation-snapshot.csv` when the working directory allows it, and name
both paths in the response.

## Guardrails

- Never call a collision confirmed on duplicate titles alone. Titles raise
  suspects; Search Console confirms.
- Never recommend consolidation without the before-snapshot captured and dated.
  Consolidation destroys the losing URL's history permanently.
- Never merge or redirect anything yourself. Name the approver from the profile
  and hand over the plan.
- Never treat a translated page as a duplicate of its source page.
- Never noindex a page that receives clicks, and never reach for noindex when a
  canonical or a rewrite would do.
- Never promise the surviving page will inherit the combined traffic. State the
  direction and the uncertainty.
- Do not diagnose site-wide duplicate content or canonical plumbing here.

**Handoff.** Send duplicate titles, canonical faults and redirect implementation
to `/technical-audit`. Send pages sliding together rather than competing to
`/content-decay`. Send the corrected keyword-to-page assignments back to
`/keyword-page-mapping`. Send the winning page's rewrite to `/page-optimiser`,
its title and description to `/meta-writer`, and its heading plan to
`/heading-architect`. Send the losing page's new informational angle to
`/content-brief`. Send the link re-pointing to `/internal-linking`. Report the
settled positions next period through `/performance-report`.
