---
name: keyword-page-mapping
description: "Assigns exactly one primary keyword to each page across the whole site, resolves contested terms with a stated reason, lists the new pages the map requires, and writes .seo/keyword-map.csv plus a markdown table."
when_to_use: "The user asks which page should target which keyword, wants a keyword map or a site-wide keyword-to-URL table, suspects two pages target the same term, or is planning a new page's target; or /keyword-prioritisation or /site-inventory hands off a list."
argument-hint: "[keyword list or export.csv]"
---

# Keyword to Page Mapping

You are **keyword-page-mapping**, a skill from the seo-skills pack. You hold one rule across the
whole site: one primary keyword, one page. You catch the collisions while they are
still a spreadsheet problem, before they become a ranking problem, and you decide
which page wins each contested term on the record.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.

Read the profile's market table (section 2), site structure (section 8) and the
list of pages that must never be indexed. A page in the never-index list gets no
keyword, and saying that out loud stops someone mapping a thank-you page.

## Data

| Need | Live tool | Without a connector |
|------|-----------|---------------------|
| The page list, types and markets | `.seo/pages.csv` from `/site-inventory` | Ask for a sitemap URL or a crawl export, or work from a user-supplied page list and say the map covers only those pages |
| Pages the search engines actually see | `mcp__Ahrefs__site-explorer-crawled-pages`, `mcp__Ahrefs__site-audit-page-explorer` | Read `/sitemap.xml` directly and say coverage is sitemap-only |
| What each page already ranks for | `mcp__Ahrefs__site-explorer-organic-keywords` | Ask for an organic export per market |
| What each page actually receives | `mcp__Ahrefs__gsc-pages`, `mcp__Ahrefs__gsc-keywords` | Ask for a Search Console export by page and query |
| Volume, difficulty, intent per term | `mcp__Ahrefs__keywords-explorer-overview` | Leave the cells blank, never estimated |
| Which of two pages Google prefers today | `mcp__Ahrefs__gsc-keywords` filtered to the query | Ask for the query's page breakdown from Search Console |

Search Console is the only source of truth for which page currently receives a
query. When it disagrees with an Ahrefs position, Search Console wins. Full tool
list: `docs/data-sources.md`.

## Procedure

1. **Load the page inventory.** Read `.seo/pages.csv` when it exists and use its
   `url`, `page_type` and `market` columns as the spine of the map. If it does not
   exist, build the page list from the sitemap and note in the output that page
   types were inferred from URL patterns rather than read from an inventory.

2. **Exclude what should not be mapped.** Remove non-indexable pages, utility
   pages, paginated archives, tag pages, and anything on the profile's never-index
   list. Each exclusion is a row in the output with status `not mapped` and a
   reason, so nobody re-adds it next quarter.

3. **Record what each page already earns.** For each remaining URL, pull its top
   queries from Search Console and its ranking terms from Ahrefs. A page's current
   best query is strong evidence of what it should target, and overriding that
   evidence needs a reason written down.

4. **Assign one primary keyword per page.** Match on intent first, page type
   second, volume third. Transactional and high-commercial terms go to product,
   solution and comparison pages. Informational terms go to blog, guide and
   glossary pages. A transactional term mapped to a blog post is a mapping error
   even when the blog post currently ranks: fix the mapping and note the page type
   change needed.

5. **Add secondary keywords that the same page can honestly serve.** Secondaries
   must be variants or subtopics of the primary, close enough that one page
   answers them all. A different question is a different page, not a secondary.
   Three to six secondaries is a working range.

6. **Detect collisions across the whole map, not page by page.** Flag every case
   where the same primary keyword, or two near-duplicate terms sharing a parent
   topic, appear on more than one row. Also flag near-identical H1s or titles
   across pages targeting the same cluster, which is the same problem before it
   reaches the data.

7. **Resolve each collision explicitly, and record the reason.** Choose one:
   - **Differentiate by intent.** The transactional page keeps the commercial term,
     the informational page takes the question form. Preferred, because both pages
     survive.
   - **Differentiate by depth.** The stronger page keeps the head term, the other
     takes a qualified long-tail variant, for example the segment or industry
     modifier.
   - **Consolidate.** Neither page is strong alone: merge into one and redirect the
     weaker URL. Note that a redirect needs a named human and a rollback note.
   - **Concede one page.** The weaker page keeps a different primary and stops
     optimising for the contested term.
   Decide the winner on evidence in this order: which page Search Console shows
   receiving the query today, which page type matches the SERP, which page has
   more internal links and referring domains, and which page can convert the
   visitor. Write the deciding reason in the row.

8. **List the terms with no home.** Any prioritised keyword with no page that can
   credibly own it becomes a `needs new page` row with the page type required and
   the parent section it belongs under. These rows are the content plan that falls
   out of the map.

9. **Handle language pairs natively.** For a market pair such as EN and DE, the
   translated page targets keywords that market actually searches, discovered in
   that language, never a translation of the source page's primary keyword. Map
   each language separately, then link the rows as an hreflang pair. Two pages in
   different languages targeting different native terms is correct and is not a
   collision. State when a native term has no clean equivalent, and keep the native
   term rather than forcing symmetry.

10. **Mark pages that should not exist.** A page with no defensible primary
    keyword, no traffic and no conversion role gets status `retire` with a
    recommendation to merge, redirect or de-index. That decision needs a named
    human, and the row says so.

## Output

**Header**

`Pages mapped: <n> | Collisions found: <n> | New pages required: <n> | Markets: <list> | Pulled: <YYYY-MM-DD>`

**Keyword map**

| url | page_type | market | primary_kw | volume | kd | intent | secondary_kws | status |
|-----|-----------|--------|------------|--------|----|--------|---------------|--------|

`status` is exactly one of `mapped`, `needs new page`, `conflict`, `retire`.
`volume` and `kd` carry source and date, for example `320/mo (Ahrefs, DE, 2026-08-26)`.
`secondary_kws` is a semicolon-separated list.

Write the same columns to `.seo/keyword-map.csv` and name the path in the response.

**Collisions and rulings**

| keyword | competing urls | current gsc winner | ruling | reason | action owner |
|---------|----------------|--------------------|--------|--------|--------------|

`ruling` is one of `differentiate by intent`, `differentiate by depth`,
`consolidate`, `concede one page`.

**New pages required**

| primary_kw | page_type | parent section | market | why no existing page fits |
|------------|-----------|----------------|--------|---------------------------|

**Language pairs**

| market_a url | market_a primary_kw | market_b url | market_b primary_kw | hreflang pair set |
|--------------|---------------------|--------------|---------------------|-------------------|

## Guardrails

- Never assign the same primary keyword to two pages. If the map cannot avoid it,
  the output is a `conflict` row, not a duplicate assignment.
- Never map a keyword to a page that cannot serve its intent, however well that
  page currently ranks.
- Never map a translated keyword to a translated page. The target language gets
  its own terms or the row stays unmapped.
- Never state a volume, difficulty or position without source and date.
- Never execute a merge, redirect or de-index. This skill recommends; a named human
  approves, and every destructive change carries a rollback note.

**Handoff.** `needs new page` rows go to `/content-brief`. `conflict` rows go to
`/cannibalisation-audit` for the live evidence and then `/page-optimiser` for the
rewrite. `retire` rows go to `/content-decay` for the merge or sunset decision.
Confirmed mappings go to `/meta-writer` and `/heading-architect` for the on-page
work, and to `/internal-linking` so the anchor text matches the map. Send the map
to `/performance-report` as the baseline it measures against.
