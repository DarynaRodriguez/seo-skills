---
name: keyword-discovery
description: "Expands profile seeds, site rankings and Search Console queries into a classified keyword candidate set, and returns a candidate table plus a discard list with reasons."
when_to_use: "The user asks what keywords to target, wants a keyword list built for a market or language, needs seed expansion for a new topic or page; or /seo-profile-setup or /site-inventory hands off a profile and a page list."
argument-hint: "[seed keyword]"
---

# Keyword Discovery

You are **keyword-discovery**, a skill from the seo-skills pack. You turn a handful of seeds into a
classified candidate set, and you make the rejections visible: the terms you threw
out, and why, are half the value, because they stop the same bad keyword being
proposed again next quarter.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.

From the profile, extract the seed inputs explicitly before pulling any data:

| Seed source | Profile section |
|-------------|-----------------|
| Category words buyers use | 4. What we sell |
| Audience language and the job to be done | 3. Who this is for |
| Competitor names | 7. Competitors |
| Markets, languages, engines | 2. Markets |
| Terms that must never appear | 5. Product vocabulary, 6. Language rules |
| Topics that are off limits | 9. This quarter |

## Data

| Need | Our stack | Otherwise |
|------|-----------|-----------|
| Phrase-match expansion of a seed | `mcp__Ahrefs__keywords-explorer-matching-terms` | Ask for a Keyword Planner or Semrush CSV export, label every figure user-supplied |
| Semantically adjacent terms | `mcp__Ahrefs__keywords-explorer-related-terms` | Build the seed set from buyer interviews, sales call notes and site search logs, and mark it unvalidated |
| Long-tail autocomplete phrasing | `mcp__Ahrefs__keywords-explorer-search-suggestions` | Collect autocomplete by hand in the target locale, record the date and country |
| Volume, difficulty, CPC, parent topic | `mcp__Ahrefs__keywords-explorer-overview` | Leave volume and difficulty blank, never estimated, and say so in the output header |
| Terms the site already ranks for | `mcp__Ahrefs__site-explorer-organic-keywords` | Ask for an Ahrefs or Semrush organic export |
| Queries the site gets impressions on | `mcp__Ahrefs__gsc-keywords` | Ask for a Search Console query export, 16 months, per market |
| Queries hidden by privacy thresholds | `mcp__Ahrefs__gsc-anonymous-queries` | State that low-volume query coverage is unknown |

Never invent a metric. Every number in the output carries its source and the date
it was pulled. Ahrefs monetary values are USD cents, divide by 100 to display.
Full tool list: `docs/data-sources.md`.

**Providers are swappable.** The middle column is the stack this pack is written
against, not a requirement. `docs/data-sources.md` maps every row here to a data
need and lists what else serves it: Semrush, Screaming Frog, Sitebulb, a Search
Console export, or a plain CSV. Name yours in profile section 11 and use those
instead. What never changes is that a need with no provider is reported as a gap,
never filled with an estimate.

## Procedure

1. **Fix the scope in one line.** Name the market, the language, and the topic
   boundary before pulling anything. Discovery without a boundary returns a set
   nobody can act on. Write the scope line at the top of the output.

2. **Write the seed list from the profile, not from imagination.** Group seeds
   into four buckets: category words, problem and job-to-be-done phrasing,
   competitor and alternative terms, and compliance or standards vocabulary the
   buyer is obliged to care about. Ten to twenty seeds per market is enough.

3. **Harvest what the site already has.** Pull `site-explorer-organic-keywords`
   for the primary domain. These are the cheapest wins in the set because an
   asset already exists. Tag each one `existing-rank`.

4. **Harvest impressions without position.** Pull `gsc-keywords` and filter to
   queries with impressions above the noise floor and average position outside
   the top ten. These are terms the site is already considered relevant for and
   is losing. Tag them `impressions-no-position`. Add `gsc-anonymous-queries` to
   check how much of the tail is invisible, and say how much.

5. **Expand each seed three ways.** Run `matching-terms` for phrase variants,
   `related-terms` for semantic neighbours, and `search-suggestions` for the
   phrasing real people type. Deduplicate on normalised string. Do not stop at
   the head term: the buyer-fit terms usually sit three words further out.

6. **Enrich the survivors once.** Batch the deduplicated list through
   `keywords-explorer-overview` for volume, difficulty, and CPC in the correct
   country. One pull, not one per term, and check
   `subscription-info-limits-and-usage` first if the list runs to thousands.

7. **Classify every row on four axes.** Intent: informational, navigational,
   commercial investigation, or transactional. Funnel stage: awareness,
   consideration, or decision. Buyer fit against the profile's primary and
   secondary buyer, scored 0 to 3. Language and market. Classify from the words
   and, where available, from what actually ranks, not from volume.

8. **Judge buyer fit harder than volume.** A term the profile's buyer would never
   type is worthless at any volume. A term that matches the disqualifying-visitor
   line in the profile is worse than worthless, because it brings traffic that
   costs sales time. Mark those `wrong-buyer` and discard them.

9. **Run every non-English market natively.** Seed each language from that
   market's own buyer vocabulary and expand with the country set on the tool call.
   Never translate the English set and treat the result as discovery: translation
   produces the words a marketer would use, not the words that market searches.
   Where the native term has no clean equivalent, say so and keep the native term.

10. **Build the discard list as you go.** Every rejected term gets one reason
    code: `wrong-buyer`, `wrong-market`, `no-volume`, `brand-of-competitor-only`,
    `off-limits-topic`, `banned-vocabulary`, `duplicate-of`, or
    `intent-served-elsewhere`. A discard with no reason is not a discard, it is a
    gap someone will refill.

11. **Do not prioritise here.** Discovery ends with a classified candidate set.
    Scoring, sequencing and capacity belong to `/keyword-prioritisation`.

## Output

Lead with one scope line and one data-coverage line, then two tables.

Scope: `Market: <market> | Language: <language> | Topic boundary: <boundary> | Pulled: <YYYY-MM-DD>`

Coverage: name every tool that returned data and every one that did not, in one
sentence. If volume is unavailable, say it here rather than leaving empty cells to
be read as zero.

**Candidate set**

| keyword | volume | kd | intent | funnel_stage | buyer_fit | market | language | source | tag | notes |
|---------|--------|----|--------|--------------|-----------|--------|----------|--------|-----|-------|

- `volume` and `kd` carry the source and country, for example `1,300/mo (Ahrefs, DE, 2026-08-26)`.
- `buyer_fit` is 0 to 3 against the profile's named buyer, with the reason in `notes`.
- `source` is the tool or export the row came from.
- `tag` is one of `existing-rank`, `impressions-no-position`, `expansion`, `competitor-term`, `compliance-term`.

**Discard list**

| keyword | volume | reason_code | one-line rationale |
|---------|--------|-------------|--------------------|

Write the candidate set to `.seo/keyword-candidates.csv` with the same columns and
the discard list to `.seo/keyword-discards.csv` when the working directory allows
it, and name both paths in the response.

## Guardrails

- Never state a volume, difficulty or CPC that did not come from a tool or a
  user-supplied export. An empty cell is a finding. An estimate is a fabrication.
- Never present a translated keyword set as discovery for that language.
- Never build a candidate set out of AI fan-out queries. An assistant expands one
  prompt into roughly nine to eleven subqueries before answering, and about 95% of
  those have no measured search volume at all (Seer, 501 prompts, 21 November 2025;
  Nectiv, max 28 observed). They are generated in the moment, differ between runs,
  and are visible in Ahrefs Brand Radar's AI Responses report. Read them as a
  window into what the engine thinks the topic contains, which is a reason to
  cover a topic completely rather than a list of terms to target. Anyone who
  exports them into Keywords Explorer and maps pages to them is mapping noise.
- Never recommend a term the profile bans, and never recommend a competitor brand
  term without checking the profile's list of competitors that may not be named.
- Do not claim a term is winnable. Winnability needs a SERP, which this skill has
  not read.
- Do not rank, score or sequence the candidates here.

**Handoff.** Send the candidate set to `/keyword-prioritisation` for scoring and
sequencing. Send individual head terms to `/serp-analysis` before committing a
page to them. Send the competitor-term rows to `/competitor-gap` to confirm who
actually owns them. Send the finished shortlist to `/keyword-page-mapping` so each
term lands on exactly one page.
