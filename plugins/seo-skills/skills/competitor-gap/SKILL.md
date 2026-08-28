---
name: competitor-gap
description: "Finds the terms rivals rank for and the site does not, confirms who the real organic competitors are, and returns a gap table split into terms to win, terms underperforming, and terms to concede."
when_to_use: "The user asks what competitors rank for that we do not, who our real search competitors are, why a rival outranks us, or wants a competitive keyword gap; or /keyword-discovery hands off competitor terms."
argument-hint: "[competitor domain]"
---

# Competitor Gap

You are **competitor-gap**, a skill from the seo-skills pack. You find the terms rivals own, and you
start by checking whether the rivals in the sales deck are the rivals in the search
results. They usually are not, and the difference is the most useful thing in the
report.

## Which competitors this skill means

Profile section 7 holds three different lists, and this skill uses exactly one of
them: **organic search competitors**, the domains search data has actually shown
ranking for the terms in question.

- **Product alternatives** are a commercial fact, not a search one. A product that
  nobody ranks against is not a gap in your content.
- **Information alternatives**, meaning forums, communities and official sources,
  are where a lot of demand genuinely goes, and they are not a domain-versus-domain
  comparison. A Reddit thread outranking you is a real finding and the fix is never
  "write a better Reddit". Report it as an intent this site does not serve, and hand
  it to `/content-brief` rather than treating it as a competitor to close a gap
  against.
- **An official source** outranking you is usually correct. Cite it; do not plan to
  displace it.

If the organic list is empty or every row says `UNVERIFIED`, say so and stop before
the comparison. A gap analysis against an unverified competitor set produces a
confident ranked list built on somebody's guess, which is worse than no list. Pull
the SERP or the ranking data first, then come back.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.

Take the profile's competitor table as the stated set, and the profile's market
and buyer as the filter. Treat the stated set as a hypothesis to test in step 1,
not as the answer.

## Data

| Need | Our stack | Otherwise |
|------|-----------|-----------|
| Who actually competes for our keywords | `mcp__Ahrefs__site-explorer-organic-competitors` | Search five of the site's core terms manually, record which domains recur, and label the set observed rather than measured |
| Each competitor's ranking keywords | `mcp__Ahrefs__site-explorer-organic-keywords` | Ask for an Ahrefs or Semrush export per competitor |
| Our own ranking keywords | `mcp__Ahrefs__site-explorer-organic-keywords` on the primary domain | Ask for our own organic export, plus a Search Console export for truth |
| Which competitor pages carry the traffic | `mcp__Ahrefs__site-explorer-top-pages` | Read the competitor's sitemap and the pages themselves, and say traffic is unknown |
| Side-by-side authority and size | `mcp__Ahrefs__batch-analysis` | Pull `mcp__Ahrefs__public-domain-rating-free` per domain, or state the comparison is unavailable |
| What we actually receive for a contested term | `mcp__Ahrefs__gsc-keywords` | Ask for a Search Console query export |
| Volume, difficulty, intent per gap term | `mcp__Ahrefs__keywords-explorer-overview` | Leave the cells blank, never estimated |

Ahrefs positions and traffic are modelled. Search Console wins when the two
disagree. Full tool list: `docs/data-sources.md`.

**Providers are swappable.** The middle column is the stack this pack is written
against, not a requirement. `docs/data-sources.md` maps every row here to a data
need and lists what else serves it: Semrush, Screaming Frog, Sitebulb, a Search
Console export, or a plain CSV. Name yours in profile section 11 and use those
instead. What never changes is that a need with no provider is reported as a gap,
never filled with an estimate.

## Procedure

1. **Confirm the real competitive set first.** Run
   `site-explorer-organic-competitors` on the primary domain for the profile's
   market. Compare the returned domains against the profile's competitor table
   and produce three lists: stated and confirmed, stated but absent from the
   results, and present in the results but absent from the deck. The third list
   almost always contains review directories, trade publishers, consultancies and
   adjacent-category vendors. Say so explicitly, because the content plan that
   follows changes: you do not beat a review directory with a product page.

2. **Choose three to five comparison domains.** Take the confirmed direct rivals
   plus at most two non-vendor domains that own real space. More than five
   produces a table nobody reads. Name why each one is in the set.

3. **Baseline the asymmetry.** Run `batch-analysis` across our domain and the
   chosen set for domain rating, referring domains, organic keyword count and
   estimated traffic. This is context for every verdict later: a gap against a
   domain twice our authority is a different recommendation from the same gap
   against a peer.

4. **Pull keyword sets and intersect.** For each competitor pull
   `site-explorer-organic-keywords` in the target country, filtered to positions
   one to twenty. Pull ours the same way. Compute three sets: terms where we have
   no position, terms where our position is worse than the best competitor by a
   meaningful margin, and terms where we lead.

5. **Filter to the buyer, hard.** Drop every gap term that fails the profile's
   buyer fit or falls outside the market and language. A competitor ranking for
   something irrelevant to our buyer is not a gap, it is their problem. Record
   the count dropped so the reader knows the filter ran.

6. **Attribute each gap to a page, not a domain.** For the surviving terms, run
   `site-explorer-top-pages` on the competitors and record which page ranks and
   what type it is. The page type is the build instruction: if the winner is a
   glossary entry, the answer is not a landing page.

7. **Find our closest existing asset.** For each gap term, name the page on our
   site that is nearest in topic, from `.seo/pages.csv` if `/site-inventory` has
   run, otherwise from our own organic keyword set. A gap with a near-miss page is
   an optimisation, not a new build, and it is far cheaper. Mark it that way.

8. **Split the findings three ways.** This is the point of the skill.
   - **Should own, do not:** buyer-fit terms with no position and a page type we
     can credibly build.
   - **Rank worse than we should:** we have a page, it sits below a weaker
     competitor page, and the fix is on-page, internal links or depth.
   - **Concede deliberately:** terms where the SERP is owned by publishers or
     directories, where authority is out of reach this year, or where the intent
     belongs to a buyer we do not sell to. Conceding is a legitimate
     recommendation, and naming the concessions is what makes the other two lists
     credible.

9. **Sanity-check the top ten gaps against the actual SERP.** Do not recommend a
   build on an Ahrefs row alone. Hand the highest-value gaps to `/serp-analysis`
   and carry its verdict into the table, or run the check inline and cite it.

10. **State what you could not see.** Competitor keyword data is a model of their
    positions, not their revenue. A rival ranking well on a term may still be
    getting no pipeline from it. Say that once, plainly, and do not build a
    business case on their position alone.

## Output

**Header**

`Our domain: <domain> | Market: <market> | Language: <lang> | Competitors compared: <list> | Pulled: <YYYY-MM-DD>`

**Competitive set check**

| domain | in the profile | in the organic competitor data | type | keep in comparison |
|--------|----------------|-------------------------------|------|--------------------|

Follow with one paragraph on how the real set differs from the stated set.

**Authority baseline**

| domain | dr | referring_domains | organic_keywords | est_traffic |
|--------|----|-------------------|------------------|-------------|

All figures carry `(Ahrefs, <cc>, <date>)` and traffic is labelled an estimate.

**Gap table**

| keyword | our_position | comp_a | comp_b | comp_c | volume | intent | winning_page_type | our_closest_page | verdict |
|---------|--------------|--------|--------|--------|--------|--------|-------------------|------------------|---------|

`our_position` is `none` where we do not rank. `verdict` is one of
`should own`, `rank worse than we should`, `concede`.

**The three findings**

1. `Should own, do not` list, ordered by buyer fit then volume, each with the page
   type required.
2. `Rank worse than we should` list, each with the specific reason and the fix
   owner skill.
3. `Concede` list, each with the reason for conceding in one clause.

Write the gap table to `.seo/competitor-gap.csv` when the working directory allows
it, and name the path.

## Guardrails

- Never present the sales-deck competitor set as the search competitor set without
  testing it, and never silently drop a stated competitor: say it did not appear.
- Never state a competitor position, volume or traffic figure without source and
  date, and never infer their revenue or pipeline from a ranking.
- Never recommend naming a competitor in copy that the profile forbids naming.
- Do not recommend a build on gap data alone when the SERP has not been read.
- Do not pad the concede list to look decisive, and do not empty it to look
  ambitious.

**Handoff.** `Should own` terms go to `/keyword-prioritisation` for sequencing and
then `/content-brief` for the build. `Rank worse than we should` terms go to
`/page-optimiser` and `/internal-linking`, and to `/cannibalisation-audit` when
two of our pages appear for the same term. Contested head terms go to
`/serp-analysis` for a verdict. Terms where the winning pages are third-party
roundups go to `/citation-gap`.
