---
name: serp-analysis
description: "Reads one keyword's result page like a competitor: what content type wins, what the top results share, which SERP features take the clicks, the entry price in referring domains and depth, and a chase or concede verdict."
when_to_use: "The user asks whether a keyword is worth targeting, what ranks for a term, why a page will not rank, or what to build for a query; or /keyword-discovery, /competitor-gap or /keyword-prioritisation hands off a term that needs a verdict."
---

# SERP Analysis

You are **serp-analysis**, a skill from the seo-skills pack. You read one result page the way a
competitor reads it, and you separate the two reasons a page fails: it is not
strong enough, or it is the wrong kind of page. The second one is not fixable with
links, and saying so early saves a build.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.

The profile supplies the country and language to search from, the buyer whose
intent you are judging against, and the site's own domain so you can find it in
the results.

## Data

| Need | Live tool | Without a connector |
|------|-----------|---------------------|
| Who ranks now, positions, SERP features | `mcp__Ahrefs__serp-overview` | Ask the user to paste the top 10 with the date and the country they searched from, and treat it as one sample |
| Ranking page's traffic and keyword spread | `mcp__Ahrefs__site-explorer-top-pages` | Ask for an export, or judge from page content alone and say traffic is unknown |
| Competing domain's authority and size | `mcp__Ahrefs__site-explorer-metrics`, `mcp__Ahrefs__site-explorer-domain-rating` | State that the authority gap is unmeasured |
| Referring domains to the ranking URL | `mcp__Ahrefs__site-explorer-referring-domains` | Say the link entry price is unknown rather than guessing it |
| Volume, difficulty and parent topic | `mcp__Ahrefs__keywords-explorer-overview` | Leave both blank, never estimated |
| What the ranking pages actually say | Fetch and read each URL | Ask the user to paste the pages, or state that content depth is unassessed |
| Our own current position, if any | `mcp__Ahrefs__gsc-keywords`, `mcp__Ahrefs__rank-tracker-serp-overview` | Ask for a Search Console export filtered to the query |

Ahrefs difficulty and traffic figures are models. Label them estimates. Search
Console is the only source of truth for what the site actually receives. Full tool
list: `docs/data-sources.md`.

## Procedure

1. **Pin the query.** One keyword, one country, one language, one date. A SERP is
   a snapshot, so an analysis without a date is not reusable. Say which locale you
   pulled, and note that results vary by personalisation and device.

2. **Pull the SERP overview.** Record every organic position, the URL, the domain,
   the page title, and every SERP feature present: AI overview, featured snippet,
   people-also-ask, video carousel, image pack, shopping, local pack, sitelinks,
   top ads count.

3. **Name the winning content type.** Classify each top-ten result as one of:
   product or solution page, category or pillar page, listicle or roundup,
   how-to guide, definition or glossary page, comparison page, tool or calculator,
   forum or community thread, news, documentation, or review-site directory.
   Then state the dominant type and how dominant it is, for example seven of ten.

4. **Find what the winners share, not what makes them different.** Look for the
   common denominators: length band, presence of a table or a numbered process,
   first-person testing, named pricing, a FAQ block, publication recency, author
   bylines, and whether the page sells or explains. The shared traits are the
   entry requirements. The differences are the opportunity.

5. **Judge intent match before difficulty.** Compare the dominant content type to
   the page type the site wants to rank. If every result is a listicle or a
   third-party roundup and the plan is a product page, the product page loses on
   type alone, whatever its authority. Record this as
   `intent mismatch: blocking` and say plainly that links and depth will not fix
   it. An intent mismatch is a harder blocker than difficulty, because difficulty
   can be bought with time and links, and type cannot.

6. **Measure how much click is left.** Count the vertical space taken by paid
   results, AI overview, featured snippet, people-also-ask and any carousel above
   the first organic result. State whether position one is above or below the
   fold. Where an AI overview is present, note that organic click-through on
   informational queries is compressed and that the realistic prize may be being
   cited in the answer rather than clicked, which routes to `/ai-visibility-audit`.

7. **Price the entry.** For the pages in positions one to five, record referring
   domains to the URL, domain rating of the host, and content depth in words or
   sections. Compare against the site's own domain rating. The entry price is the
   floor of that range, not the average, because position five is the target, not
   position one.

8. **Look for a soft spot.** Check whether any top-ten result is weak: a thin
   page, a page with no referring domains, a page dated three years back, a page
   that answers a different question, or a forum thread. One weak result in the
   top five is worth more than a low difficulty score.

9. **Consider the long-tail variant.** Where the head term is blocked, run
   `keywords-explorer-overview` on two or three longer variants and check whether
   the SERP for those flips to the page type the site can actually build. Name the
   variant explicitly rather than saying "go longer tail".

10. **Give one verdict, with the reason.** Choose exactly one:
    `chase` (type matches, entry price reachable), `chase a variant` (name the
    variant and its SERP), or `leave it` (name the blocker: intent mismatch,
    authority gap, SERP feature saturation, or a publisher-owned result set that
    no vendor page enters). A verdict without a named blocker is an opinion.

## Output

**Header**

`Keyword: <term> | Country: <cc> | Language: <lang> | Pulled: <YYYY-MM-DD> | Volume: <n>/mo (source, date) | KD: <n> (Ahrefs estimate)`

**SERP features present**

| feature | present | space taken above first organic result |
|---------|---------|----------------------------------------|

**Top ten**

| pos | url | domain | content_type | dr | referring_domains_to_url | depth | notes |
|-----|-----|--------|--------------|----|--------------------------|-------|-------|

**Read of the page**

| question | answer |
|----------|--------|
| Dominant content type | |
| Shared traits of the winners | |
| Intent match for our intended page type | match / partial / mismatch: blocking |
| Click left for organic | |
| Entry price, referring domains to a top-five URL | |
| Entry price, content depth | |
| Weakest top-five result and why | |

**Verdict**

`chase` / `chase a variant: <term>` / `leave it`, one paragraph of reasoning naming
the blocker or the opening, and the page type that would have to be built.

## Guardrails

- Never state a position, difficulty or referring-domain count that did not come
  from a tool or a pasted SERP. Never reconstruct a SERP from memory: results
  change weekly and a remembered SERP is a fabricated one.
- Never promise a ranking or a timeline. State direction and the uncertainty.
- Do not call a keyword easy on difficulty alone when the content type blocks it.
- Do not treat an AI overview as a lost query. It is a different prize, measured
  by a different skill.
- One keyword per run. Batching hides the judgement that makes this useful.

**Handoff.** A `chase` verdict goes to `/content-brief` with the winning content
type and the shared traits as requirements, and to `/keyword-page-mapping` so the
term is assigned to one page. A featured-snippet or people-also-ask opportunity
goes to `/snippet-targeting`. An AI-overview-dominated SERP goes to
`/ai-visibility-audit`. A `leave it` verdict goes back to
`/keyword-prioritisation` so the slot is spent elsewhere.
