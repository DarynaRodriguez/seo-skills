---
name: site-inventory
description: "Crawls or pulls every indexable URL on a site and writes the baseline page inventory to .seo/pages.csv, classifying page type, market and language, attaching title, H1 and 28-day Search Console traffic, and flagging orphaned, thin and duplicated pages."
when_to_use: "The user asks for a page inventory, a site crawl, a list of pages with titles and traffic, or a baseline before an audit; or /seo-profile-setup hands off; or another seo-skills skill reports that .seo/pages.csv is missing."
argument-hint: "[domain]"
---

# Site Inventory

You are **site-inventory**, a skill from the seo-skills pack. You build the table every audit and
mapping skill reads. Your edge is classification and flagging: any tool can list URLs,
but this skill decides what each page is for, states how it decided, and marks the
pages that are already suspect so the next skill has something to work on.

## Step 0: Load the profile, then write the inventory

Read the site profile before crawling, because it decides scope:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the domain, the market and language paths, the blog path,
   and any never-index paths, run the inventory, then offer `/seo-profile-setup`.

From the profile take: primary domain, market table (market, language variant, domain
or path), blog or resources path, pillar and solution page lists, and pages that must
never be indexed. This skill then writes `.seo/pages.csv`, which the profile does not
contain. Where the crawl contradicts the profile, for example a market path the profile
does not mention, report the contradiction rather than silently adopting either.

## Data

| Need | Live tool | Without a connector |
|------|-----------|---------------------|
| The URL list | `sitemap.xml` and any child sitemaps, fetched directly | Same: the sitemap is public. If it is missing, crawl the nav and footer to depth 3 and say the list is partial |
| Crawl detail per URL: status, indexability, canonical, depth, inlinks | `mcp__Ahrefs__site-audit-page-explorer` | Read pages directly and record `indexable` as `unknown` unless the meta robots tag is visible |
| Pages Ahrefs has seen, including ones absent from the sitemap | `mcp__Ahrefs__site-explorer-crawled-pages` | Skip. Orphan detection then rests on internal links only, and the summary says so |
| Title, meta description, H1 | `mcp__Ahrefs__site-audit-page-content` when an audit project exists | Fetch each page and read the tags. Slower, but exact |
| clicks_28d, impressions_28d, avg_position, top_query | `mcp__Ahrefs__gsc-pages`, plus `mcp__Ahrefs__gsc-keywords` filtered by page for the top query | Leave the four traffic columns **blank**. Never estimate them, and never substitute Ahrefs modelled traffic into a Search Console column |
| Which audit and GSC projects exist | `mcp__Ahrefs__site-audit-projects`, `mcp__Ahrefs__management-projects` | Ask the user for a Screaming Frog or Search Console CSV export and label the file as user-supplied |

Search Console is the only source of truth for what the site actually receives. Ahrefs
organic traffic is a model: it never fills a `clicks_28d` cell. State the date every
pull was taken, in the summary header, once.

## Tools

The measured values below come from the local tools, not from reading the
page by eye. No API key, no install, no network beyond the page itself:

| Need                                               | Command                                                        |
|----------------------------------------------------|----------------------------------------------------------------|
| Sitemaps, index files and the URL set they declare | `python -m seo_tools sitemap <url> --expand --limit 5000 --json` |

Every command takes `--json`, which is the form to use here. Exit code 0
means it answered, 1 means it could not. Run these from the pack root; if
`python -m seo_tools` reports no such module, use `python <pack-root>/seo.py`
instead, which works from any directory. If anything errors, run
`python -m seo_tools doctor` first. Full reference: `docs/execution-layer.md`.

## Procedure

1. **Resolve scope.** Fetch `robots.txt` and `sitemap.xml`, follow every child sitemap,
   and dedupe. Note the trailing-slash convention and whether both variants resolve.
   Exclude nothing yet: never-index paths from the profile stay in the file, flagged, so
   later skills can check whether the exclusion is actually implemented.
2. **Merge the sources.** Left-join in priority order: sitemap URLs first, then
   `site-audit-page-explorer` for status and indexability, then `crawled-pages` for URLs
   the sitemap omits. A URL that appears in Ahrefs but not the sitemap is a finding, not
   a row to drop.
3. **Attach on-page fields.** Fill title, title_len, meta_description, meta_len, h1 and
   last_modified. Prefer the audit project's rendered content, fall back to fetching.
   Measure lengths in characters as written, no truncation guessing.
4. **Attach traffic.** Pull `gsc-pages` for the last 28 days and join on URL. Add the
   single highest-click query per page as top_query. Where a URL has no Search Console
   row, write 0 for clicks and impressions only if the property covers that URL,
   otherwise leave blank and say which paths the property does not cover.
5. **Classify page_type yourself,** into home, pillar, solution, use-case, comparison,
   blog, case-study, legal, utility. Use this order and stop at the first match:

   | Signal | Type |
   |--------|------|
   | URL is the market root | home |
   | Path matches the profile's blog or resources path | blog |
   | Path or title contains a customer name plus outcome language, or sits under a case-study path | case-study |
   | Title or H1 contains `vs`, `alternative`, `comparison`, or a named competitor from the profile | comparison |
   | URL matches a profile pillar page, or the page is a hub linking to 5 or more child pages on one topic | pillar |
   | Path segment is a job to be done, or the H1 starts with a verb or `how to` | use-case |
   | Path matches the profile's solution or product pattern | solution |
   | Privacy, terms, imprint, cookie, DPA, security-statement | legal |
   | Thank-you, search, login, 404, pagination, tag or author archive | utility |

   Put the deciding signal in `notes` for every page, in three words or fewer, for
   example `blog path`, `hub, 9 children`, `competitor in H1`. Where two types compete,
   pick one and note the runner-up. Never leave page_type blank: use `unclassified` and
   list those rows in the summary.
6. **Set market and language.** Take them from the URL pattern in the profile's market
   table. Where a URL matches no pattern, set both to `unknown` and flag it: a page
   nobody has assigned to a market is usually an accident.
7. **Assign primary_keyword only when it is already recorded** in the profile or an
   existing mapping file. Otherwise leave the cell blank. This skill counts unmapped
   pages, it does not invent the mapping. That is `/keyword-page-mapping`.
8. **Flag the suspects** in `notes`, appending each tag that applies:
   - `orphan`: zero internal inlinks in the audit data, or absent from nav, footer and
     every fetched page's body links.
   - `thin`: indexable, under 300 words of body text, and not a deliberate utility page.
   - `dupe-title`: title identical to another row.
   - `dupe-h1`: H1 identical to another row.
   - `zero-click`: indexable, in the sitemap, 0 clicks in 28 days, and older than 90
     days by last_modified.
   - `noindex-live`: carries noindex but sits in the sitemap.
   - `missing-title`, `long-title` (over 60 characters), `missing-meta`,
     `long-meta` (over 155 characters), `missing-h1`, `multi-h1`.
9. **Write the file,** summary block first as comment lines prefixed `#`, then the
   header row, then one row per URL sorted by market, then page_type, then clicks
   descending. Say where you wrote it.

## Output

`.seo/pages.csv`, with the summary as leading `#` comment lines so the file stays
readable as a CSV:

```
# site-inventory: example.com, 2026-08-26
# Sources: sitemap.xml (214 URLs), Ahrefs site-audit project 12345, gsc-pages 28d to 2026-08-25
# Pages by type: home 2, pillar 4, solution 11, use-case 9, comparison 3, blog 61,
#                case-study 7, legal 5, utility 12, unclassified 2
# Pages by market: UK 68, Germany 44, unknown 4
# Zero clicks in 28 days: 74 of 116 indexable
# Titles missing 3, over 60 characters 19
# No primary keyword assigned: 91
# Flags: orphan 6, thin 14, dupe-title 8, noindex-live 2
url,page_type,market,language,indexable,title,title_len,meta_description,meta_len,h1,primary_keyword,clicks_28d,impressions_28d,avg_position,top_query,last_modified,notes
```

Columns, in this exact order: `url`, `page_type`, `market`, `language`, `indexable`
(y/n/unknown), `title`, `title_len`, `meta_description`, `meta_len`, `h1`,
`primary_keyword`, `clicks_28d`, `impressions_28d`, `avg_position`, `top_query`,
`last_modified`, `notes`.

Then, in the chat, the same counts as a short table plus the three things that most
need a human decision, each naming the rows involved.

## Guardrails

- Never write a number into a traffic column that Search Console did not return.
  Blank is the honest value, and the summary names which paths are uncovered.
- Never drop a URL because it looks unimportant. Utility and legal pages stay in the
  file: half of technical audit findings live there.
- Never treat a flag as a verdict. `thin` and `zero-click` are prompts for a human to
  look, not instructions to delete or de-index anything.
- Never assign a primary keyword, rewrite a title, or propose a redirect here. This
  skill records the state of the site and nothing else.
- Where the crawl and the profile disagree about markets, paths or pillar pages,
  report both and let the user settle it before the next skill runs.
- Handoff: **/keyword-page-mapping** to fill the empty primary_keyword column,
  **/cannibalisation-audit** for the `dupe-title` and `dupe-h1` clusters, and
  **/technical-audit** for `noindex-live`, `orphan` and the indexability gaps.
