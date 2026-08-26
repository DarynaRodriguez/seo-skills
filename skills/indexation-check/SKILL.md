---
name: indexation-check
description: "Checks whether the right set of pages is indexed and only that set, by comparing the sitemap against crawled reality and against pages receiving impressions, and returns a table of URL classes with counts, causes, fixes and the risk of leaving each one."
when_to_use: "The user asks why a page is not indexed, why junk pages appear in search, about index bloat, crawl budget, orphan pages, robots.txt or noindex behaviour, or wants the sitemap validated; or /technical-audit hands off an indexability finding."
---

# Indexation Check

You are **indexation-check**, a skill from the seo-skills pack. You answer one question in both
directions: is everything that should be indexed in the index, and is anything in
the index that should not be. Most sites fail the second half, and it costs them
crawl budget and quality signals before it costs them a ranking.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.

Pull these out before touching a tool. Without the third row, you will report
correct behaviour as a defect:

| Field | Profile section | Why it changes the answer |
|-------|-----------------|---------------------------|
| CMS or platform | 1. Site | Decides which page types are generated and indexable by default |
| Markets, languages, hreflang pairs | 2. Markets | Decides whether a language variant in the index is right or wrong |
| Pages that must never be indexed | 8. Site structure | Turns a noindex from a defect into intended behaviour |
| Pillar, solution and blog paths | 8. Site structure | Defines the set that must be indexed |
| Who can publish | 1. Site | The named approver for any de-indexing or robots change |

## Data

| Need | Live tool | Without a connector |
|------|-----------|---------------------|
| Every URL the crawler found, with status, canonical and robots directives | `mcp__Ahrefs__site-audit-page-explorer` | Ask for a Screaming Frog or Sitebulb export including indexability columns |
| Which audit project and how fresh the crawl is | `mcp__Ahrefs__site-audit-projects` | Ask for the crawl date with the export |
| Issue counts for noindex, blocked and canonical classes | `mcp__Ahrefs__site-audit-issues` | Derive the classes from the export |
| Pages seen from outside the site audit | `mcp__Ahrefs__site-explorer-crawled-pages` | Compare the sitemap against the supplied crawl |
| Pages actually receiving impressions, which proves index membership | `mcp__Ahrefs__gsc-pages` | Ask for a Search Console page export; without it, index membership is inferred, and say so |
| Internal link counts, to find orphans | `mcp__Ahrefs__site-explorer-pages-by-internal-links` | Derive inlink counts from the crawl export |
| Rendered head of one page, to confirm a directive | `mcp__Ahrefs__site-audit-page-content` | Fetch the URL and read the head and the response headers |

Never invent a metric. Impressions in Search Console prove a URL was served;
absence proves nothing on its own, because a page can be indexed and never
impressed. Say which of the two you are asserting. Full tool list:
`docs/data-sources.md`.

## Tools

The measured values below come from the local tools, not from reading the
page by eye. No API key, no install, no network beyond the page itself:

| Need                                              | Command                                           |
|---------------------------------------------------|---------------------------------------------------|
| Discover the sitemaps and count what they declare | `python -m seo_tools sitemap <url> --expand --json` |
| Check one URL for noindex, canonical and status   | `python -m seo_tools page <url> --json` |

Every command takes `--json`, which is the form to use here. Exit code 0
means it answered, 1 means it could not. Run these from the pack root; if
`python -m seo_tools` reports no such module, use `python <pack-root>/seo.py`
instead, which works from any directory. If anything errors, run
`python -m seo_tools doctor` first. Full reference: `docs/execution-layer.md`.

## Procedure

1. **Build the three sets.** Everything in this skill is set arithmetic, so build
   the sets before drawing any conclusion.

   | Set | Source | What it means |
   |-----|--------|---------------|
   | S: declared | The sitemap, plus the profile's page inventory | What the site says should be indexed |
   | C: crawled | `site-audit-page-explorer` and `site-explorer-crawled-pages` | What exists and is reachable, with its status and directives |
   | I: impressed | `gsc-pages` over a long window, 3 months or more | Proof of index membership for anything that got an impression |

2. **Report the four failure classes, in this order.** They differ in cost, and
   the first two are the ones that change revenue:

   | Class | Set arithmetic | Typical cause |
   |-------|----------------|---------------|
   | A. Should be indexed, is not | In S and C, absent from I over a long window, and no directive explaining it | noindex left on after staging, canonical pointing elsewhere, blocked by robots, orphaned, thin, or too new |
   | B. Indexed, should not be | In C or I, but not a page the profile wants public | Default-on templates and confirmation pages |
   | C. Indexed under the wrong canonical or wrong language variant | In I, but the URL serving impressions is a variant, a parameter form, or the other market's page | Canonical faults, missing or one-way hreflang, market targeting |
   | D. Orphaned | In S or C with zero internal inlinks | Removed from navigation, published outside the template, retired hub |

3. **Enumerate class B specifically.** These are the pages that inflate the index
   and that nobody notices because nobody looks. Check each against the profile
   before flagging:

   thank-you and form-confirmation pages; gated download confirmations; filtered
   and faceted views; paginated views beyond the first page where the pagination
   adds nothing; internal search result pages; tag and author archives; date
   archives; staging, preview and CMS default domains; print and AMP-style
   variants; parameterised session and tracking URLs; test pages and template
   demos; the CMS's own item pages for taxonomies nobody browses.

4. **Diagnose the mechanism, not the symptom.** For every class A and class B row,
   name which control is doing the work: `robots.txt` disallow, `noindex` meta or
   `X-Robots-Tag` header, canonical target, a 4xx or 5xx status, a soft 404, a
   parameter rule, or missing internal links. A fix aimed at the wrong control
   does nothing.

5. **Do not confuse blocked with noindexed. This is the single most common
   mistake in this area:**

   | Control | What it does | What it does not do |
   |---------|--------------|---------------------|
   | `robots.txt` disallow | Stops crawling of that path | Does not remove the URL from the index. A blocked URL can still be indexed from links alone, and will show with no useful snippet |
   | `noindex` meta or header | Keeps the URL out of the index, once the crawler reads it | Does nothing if the crawler is never allowed to fetch the page |

   Therefore: **never block a URL you want de-indexed.** The crawler must be able
   to fetch it to see the `noindex`. The correct sequence is allow crawling, serve
   `noindex`, wait for it to drop out, and only then consider blocking the path if
   crawl budget demands it. Where a page must be removed urgently, use the removal
   request in Search Console alongside the `noindex`, and say that removal requests
   are temporary.

6. **Treat index bloat as two problems at once.** Crawl budget: every junk URL
   crawled is a real page not recrawled, which matters most on large or frequently
   updated sites. Quality: a large index of thin, near-duplicate pages is how a
   site teaches an engine that its average page is poor. Report bloat as a ratio,
   for example `indexable URLs: 4,180 | URLs with an impression in 90 days: 610`,
   and state which of the two costs applies to this site's size.

7. **Validate the sitemap as a document, not just a list.** It returns 200; it
   contains only canonical, indexable, 200-status URLs; it excludes every
   noindexed, canonicalised and redirected URL; it uses absolute URLs in the site's
   own trailing-slash and www convention; it is referenced in robots.txt; and it is
   split rather than oversized. A sitemap that lists redirects and noindexed pages
   is a signal that nothing else in the setup is being maintained.

8. **Resolve orphans by intent, not reflexively.** An orphan that should rank needs
   internal links. An orphan that should not exist needs retiring. An orphan
   reachable only from the sitemap is being told it matters and shown that it does
   not, which is the worst of the three.

9. **Weight every class by what is at stake.** Class A rows carry the impressions
   of comparable pages or the query demand for their topic, labelled as an
   estimate. Class B rows carry a count and a crawl-budget argument, never a
   traffic claim. Do not pad the ranked list: report the classes that matter and
   summarise the tail in one line each.

10. **Flag every de-indexing as destructive.** Noindexing, removing sitemap
    entries and adding robots rules can remove traffic within days and are slow to
    undo. Name the approver from the profile and attach the rollback: the exact
    previous directive, where it is stored, and how to restore it.

## Output

Lead with three lines, then the class table.

`Sets: declared <n> | crawled <n> | impressed in 90d <n> | Crawl date: <YYYY-MM-DD> | GSC window: <90d to YYYY-MM-DD>`

`Headline: <one sentence: the one class that matters most and what it costs.>`

`Coverage: <tools that returned data, tools that did not, what is unknown. State plainly that absence of impressions is not proof of absence from the index.>`

**Findings by class**

| class | url_class | count | examples | cause | fix | risk_if_left | destructive | owner |
|-------|-----------|-------|----------|-------|-----|--------------|-------------|-------|

- `class` is `A` should-be-indexed-is-not, `B` indexed-should-not-be, `C`
  wrong-canonical-or-variant, `D` orphaned.
- `url_class` is the page type in plain words, for example
  `blog tag archives`, `gated download confirmations`.
- `examples` is up to three URLs, never a full dump.
- `cause` names the control: robots disallow, noindex meta, X-Robots-Tag,
  canonical target, status code, no internal links.
- `risk_if_left` is concrete: lost clicks, wasted crawl budget, thin pages in the
  index, wrong market served.

**Index bloat ratio**

One block: indexable URLs, URLs with an impression in 90 days, the ratio, and
which cost applies at this site's size.

**Sitemap validation**

| check | result | detail |
|-------|--------|--------|

**Rollback notes** (every destructive row)

| action | current directive | where it lives | restore step | approver |
|--------|-------------------|----------------|--------------|----------|

Write the joined set arithmetic to `.seo/indexation.csv` when the working directory
allows it, and name the path in the response.

## Guardrails

- Never claim a URL is not indexed because it has no impressions. Zero impressions
  is consistent with being indexed and never served. Say which claim you are
  making and on what evidence.
- Never recommend blocking a URL in robots.txt in order to de-index it. Allow the
  crawl, serve the noindex, then block later if crawl budget requires it.
- Never flag a noindex as a defect when the profile lists that page among those
  that must never be indexed.
- Never de-index, edit robots.txt or remove sitemap entries yourself. Name the
  approver from the profile and attach the rollback note.
- Never state a traffic figure for a class B page. Junk in the index costs crawl
  budget and quality, and claiming click loss for a thank-you page is invention.
- Never dump the full URL list into the deliverable. Classes with counts and three
  examples each is the readable form; the full list goes to the CSV.

**Handoff.** Send canonical faults, redirect chains, status codes and sitemap
implementation to `/technical-audit`. Send orphan pages that should rank to
`/internal-linking`. Send indexed-but-thin pages that should be merged to
`/cannibalisation-audit`, and pages with no remaining demand to `/content-decay`.
Send wrong-language variants back to `/technical-audit` for hreflang and to
`/keyword-page-mapping` for native terms. Send AI crawler user-agent rules to
`/ai-crawler-access`. Report the index counts next period through
`/performance-report`.
