# Data sources

## You cannot do this work without data

There is no version of this pack that produces good output from nothing. Every
skill here answers a question that needs evidence: what does this site actually
receive, who actually ranks, what do the engines actually cite. Without a source
for that, a skill can tell you how to think about a problem, and it will refuse to
tell you the answer.

So plugging in data is not an optional upgrade. It is the setup step.

What is genuinely optional is **which** tool you plug in. The skills are written
against a small set of **data needs**, and each need can be served by whatever you
already pay for, or by a CSV export, or in a few cases by the tools in this repo.
Switching from Ahrefs to Semrush is a line in your profile, not a rewrite.

## The needs

Every skill's Data table is written in terms of these. Nothing else.

| Need | Answers | Skills that need it |
|------|---------|--------------------|
| `page` | What one URL actually serves: title, headings, canonical, schema, rendering | Most on-page skills |
| `robots-sitemap` | Which crawlers may fetch what, and which URLs the site declares | `ai-crawler-access`, `indexation-check`, `technical-audit` |
| `crawl` | Every URL with status, title, meta, canonical, depth and inlinks | `technical-audit`, `site-inventory`, `indexation-check`, `internal-linking` |
| `traffic` | Clicks, impressions, CTR and position, per query and per page | `performance-report`, `content-decay`, `cannibalisation-audit`, `keyword-prioritisation`, `meta-writer` |
| `keywords` | Volume, difficulty and intent for a term | `keyword-discovery`, `keyword-prioritisation`, `demand-trends` |
| `serp` | Who ranks for a term now, and which features take the space | `serp-analysis`, `competitor-gap`, `snippet-targeting` |
| `backlinks` | Referring domains, anchors, and what points at a page | `citation-gap`, `competitor-gap` |
| `ai-visibility` | How often a brand is named in AI answers, and its share of voice | `ai-visibility-audit`, `prompt-panel` |
| `ai-citations` | Which URLs AI answers cite for a question | `citation-gap`, `geo-rewrite` |
| `ai-crawler-hits` | Which AI bots fetched which pages | `ai-crawler-access`, `ai-visibility-audit` |
| `vitals` | Field performance data for real visitors | `technical-audit` |
| `analytics` | Sessions and conversions by channel | `performance-report` |

Two of these are served by this repo with no account at all: `page` and
`robots-sitemap`. Two more can be served by a file export rather than an API:
`crawl` and `traffic`. That is the free floor, and it is enough to run a real
technical audit and a real decay analysis.

## Providers

| Provider | Serves | How | Cost |
|----------|--------|-----|------|
| **seo-tools** (in this repo) | `page`, `robots-sitemap`, `crawl`, `traffic` | `python -m seo_tools …` | free, no account |
| **Ahrefs MCP** | `keywords`, `serp`, `backlinks`, `traffic`, `crawl`, `ai-visibility`, `ai-citations` | MCP connector | paid |
| **Peec AI MCP** | `ai-visibility`, `ai-citations`, `ai-crawler-hits` | MCP connector | paid |
| **Semrush** | `keywords`, `serp`, `backlinks`, `crawl` | CSV export, or MCP if your account exposes one | paid |
| **Screaming Frog** | `crawl` | CSV export into `seo_tools crawl` | free to 500 URLs, then paid |
| **Sitebulb** | `crawl` | CSV export into `seo_tools crawl` | paid |
| **Google Search Console** | `traffic` | CSV export into `seo_tools gsc`, or the API | free |
| **PageSpeed Insights or CrUX** | `vitals` | API, needs a key | free |
| **GA4** | `analytics` | Export or API | free |
| **Any CSV or spreadsheet** | `crawl`, `traffic`, `keywords` | `--columns` names the columns | free |

### The stack this pack is written against

**Search Console, Ahrefs and Peec AI**, plus the built-in tools. That is what the
skills name first, and it is what we use.

Being straight about why: Search Console because it is the only source of what a
site actually received rather than a model of it, and it is free. Ahrefs because
one connector covers keywords, SERPs, backlinks, crawl and AI answers, which
avoids reconciling four vendors' numbers. Peec AI because the AI-visibility lane
needs prompt-level data with sentiment and crawler hits, and general SEO suites
treat that as a bolt-on.

None of that makes the alternatives wrong. If you have Semrush, use Semrush. The
skills will work and the output will be as good, provided you tell the profile
which provider serves which need so nobody has to guess.

### The floor, with no paid tool at all

```bash
python -m seo_tools crawl screamingfrog.csv     # crawl: any exporter
python -m seo_tools gsc queries.csv             # traffic: the free GSC export
python -m seo_tools page https://example.com/   # page
python -m seo_tools robots https://example.com/ # robots-sitemap
```

That covers `crawl`, `traffic`, `page` and `robots-sitemap`. What you will not
have is `keywords`, `serp`, `backlinks` and the AI-answer needs. Those skills will
ask you for an export or tell you the figure is unknown. They will not estimate.

## Declaring your providers

Section 11 of the profile (`profiles/PROFILE.template.md`) is where you say what
you have. A skill reads it at Step 0 and uses whatever is named, so nothing
depends on a hardcoded vendor:

```markdown
## 11. Data providers

| Need | Provider | How to reach it |
|------|----------|-----------------|
| crawl | Screaming Frog | Weekly export at ~/crawls/latest.csv, read with `seo_tools crawl` |
| traffic | Google Search Console | Manual CSV export, read with `seo_tools gsc` |
| keywords | Semrush | CSV export from Keyword Magic Tool |
| serp | Semrush | Manual, paste the top 10 with date and country |
| backlinks | none | Skills say the figure is unknown |
| ai-visibility | none | Run the prompts by hand, sample of one, record the date |
```

Say `none` where you have nothing. That is a better answer than a provider you do
not really have, because it tells the skill to state a gap instead of trying.

## Provider detail

### seo-tools, in this repo

| Need | Command |
|------|---------|
| `page` | `python -m seo_tools page <url>` |
| `robots-sitemap` | `python -m seo_tools robots <url>`, `python -m seo_tools sitemap <url> --expand` |
| `crawl` | `python -m seo_tools crawl <export.csv>` |
| `traffic` | `python -m seo_tools gsc <export.csv> [--compare <earlier.csv>]` |

Full reference: [`execution-layer.md`](execution-layer.md). Both import commands
recognise the common exporters by their headers and take `--columns` for anything
they do not.

### Screaming Frog, Sitebulb, or any crawler

Export to CSV and hand it to `seo_tools crawl`. Screaming Frog's **Internal, All**
export and Sitebulb's URL export are recognised by their headers. Anything else
works with `--columns url,status,title,meta_description,canonical,word_count,inlinks`.

What the crawl answers on its own, with no API: status distribution, broken URLs
ordered by inlinks, redirect chains, duplicate titles, descriptions and H1s across
indexable pages only, missing titles and descriptions, canonicals pointing
elsewhere, orphans, and thin pages against a threshold you set.

Two things to know. Duplicates and missing-field counts deliberately ignore
non-indexable pages, because a duplicate title on a noindexed thank-you page is
not competing with anything. And the thin-page threshold is an argument rather
than a rule: a 200-word pricing page can be exactly right.

### Google Search Console

The free export is the highest-value data in this list, and the only source of
what a site actually receives. `seo_tools gsc` recognises the export header in 14
languages and takes `--columns` for the rest.

One limit worth planning around: the UI exports queries and pages as separate
files, so it cannot answer which query landed on which page. Cannibalisation needs
both dimensions on one row, which means the API or Looker Studio. The tool says
so rather than guessing.

### Ahrefs MCP

Call `mcp__Ahrefs__doc` before first use of an unfamiliar endpoint.

**Keywords**

| Job | Tool |
|-----|------|
| Volume, difficulty, CPC, intent for known terms | `mcp__Ahrefs__keywords-explorer-overview` |
| Expand a seed by phrase match | `mcp__Ahrefs__keywords-explorer-matching-terms` |
| Semantically related terms | `mcp__Ahrefs__keywords-explorer-related-terms` |
| Autocomplete-style long tail | `mcp__Ahrefs__keywords-explorer-search-suggestions` |
| Which country the demand sits in | `mcp__Ahrefs__keywords-explorer-volume-by-country` |
| Seasonality and trend | `mcp__Ahrefs__keywords-explorer-volume-history` |

**SERP and competitors**

| Job | Tool |
|-----|------|
| Who ranks now, with features | `mcp__Ahrefs__serp-overview` |
| Domains competing for the same keywords | `mcp__Ahrefs__site-explorer-organic-competitors` |
| A domain's ranking keywords | `mcp__Ahrefs__site-explorer-organic-keywords` |
| A domain's best pages | `mcp__Ahrefs__site-explorer-top-pages`, `mcp__Ahrefs__site-explorer-pages-by-traffic` |
| Many domains at once | `mcp__Ahrefs__batch-analysis` |
| Tracked-keyword positions | `mcp__Ahrefs__rank-tracker-overview`, `mcp__Ahrefs__rank-tracker-serp-overview` |

**Traffic, via Search Console**

| Job | Tool |
|-----|------|
| Query-level clicks, impressions, position | `mcp__Ahrefs__gsc-keywords` |
| Page-level performance | `mcp__Ahrefs__gsc-pages` |
| One query over time | `mcp__Ahrefs__gsc-keyword-history` |
| One page over time | `mcp__Ahrefs__gsc-page-history` |
| Many pages over time | `mcp__Ahrefs__gsc-pages-history` |
| Site totals over time | `mcp__Ahrefs__gsc-performance-history` |
| Position distribution and CTR curve | `mcp__Ahrefs__gsc-performance-by-position`, `mcp__Ahrefs__gsc-ctr-by-position` |
| Country and device splits | `mcp__Ahrefs__gsc-metrics-by-country`, `mcp__Ahrefs__gsc-performance-by-device` |

Search Console is the only source of truth for what a site actually receives.
Ahrefs organic traffic is a model. When the two disagree, Search Console wins.

**Crawl, via Site Audit**

| Job | Tool |
|-----|------|
| Which audit projects exist | `mcp__Ahrefs__site-audit-projects` |
| Issue list by severity | `mcp__Ahrefs__site-audit-issues` |
| Per-URL crawl detail | `mcp__Ahrefs__site-audit-page-explorer` |
| Rendered content of one page | `mcp__Ahrefs__site-audit-page-content` |
| Pages Ahrefs has seen | `mcp__Ahrefs__site-explorer-crawled-pages` |
| Internal link counts | `mcp__Ahrefs__site-explorer-pages-by-internal-links`, `mcp__Ahrefs__site-explorer-linked-anchors-internal` |

**Backlinks**

| Job | Tool |
|-----|------|
| Domain Rating, now and over time | `mcp__Ahrefs__site-explorer-domain-rating`, `mcp__Ahrefs__site-explorer-domain-rating-history` |
| Backlink and referring-domain totals | `mcp__Ahrefs__site-explorer-backlinks-stats`, `mcp__Ahrefs__site-explorer-referring-domains` |
| Individual links | `mcp__Ahrefs__site-explorer-all-backlinks` |
| Links pointing at dead URLs | `mcp__Ahrefs__site-explorer-broken-backlinks` |
| Anchor-text distribution | `mcp__Ahrefs__site-explorer-anchors` |

**AI answers, via Brand Radar**

| Job | Tool |
|-----|------|
| How often a brand appears in AI answers | `mcp__Ahrefs__brand-radar-mentions-overview`, `-mentions-history` |
| Share of voice | `mcp__Ahrefs__brand-radar-sov-overview`, `-sov-history` |
| Which domains and pages get cited | `mcp__Ahrefs__brand-radar-cited-domains`, `mcp__Ahrefs__brand-radar-cited-pages` |
| The raw AI answers | `mcp__Ahrefs__brand-radar-ai-responses` |
| Tracked prompts | `mcp__Ahrefs__management-brand-radar-prompts` |

**Housekeeping.** `mcp__Ahrefs__management-projects`, `-project-keywords`,
`-locations` to resolve project and location IDs.
`mcp__Ahrefs__subscription-info-limits-and-usage` before a large pull, so a run
does not burn a month of units.

**Units.** Every monetary value (`value`, `org_cost`, `paid_cost`,
`traffic_value`) is in USD cents. Divide by 100 before display.

**Rendering.** When a response carries `render_with` in its metadata, call that
render tool (`render-data-table`, `render-scorecard`, `render-time-series-chart`)
rather than dumping the raw rows.

### Peec AI MCP

| Job | Tool |
|-----|------|
| Which projects exist, and their profile | `list_projects`, `get_project_profile` |
| Tracked prompts | `list_prompts`, `list_prompt_suggestions` |
| Brand visibility, SoV, sentiment, position | `get_brand_report` |
| Which domains get retrieved and cited | `get_domain_report` |
| Which URLs get retrieved and cited | `get_url_report` |
| The actual AI conversations | `list_chats`, `get_chat`, `get_chats_report` |
| Prioritised recommendations | `get_actions` (scope `overview` first, then `owned` / `editorial` / `reference` / `ugc`) |
| How buyers describe the brand | `get_brand_perception_brand_attributes`, `get_brand_perception_attribute_rankings`, `get_brand_perception_competitive_breakdown`, `get_brand_perception_attribute_sources` |
| AI crawler hits on the site | `get_agent_visits`, `list_bots` |
| What a cited page actually says | `get_url_content` |
| Topics, tags, brands, competitors | `list_topics`, `list_tags`, `list_brands` |

**IDs are opaque.** Copy `pr_…`, `to_…`, `tg_…` identifiers verbatim from a tool
result. Never shorten, complete, or reconstruct one from memory.

**Units.** `visibility`, `share_of_voice`, `retrieved_percentage` are 0 to 1
ratios, so multiply by 100 to display. `sentiment` is 0 to 100, where most brands
land between 65 and 85 and below 50 is a problem. `position` is a rank, lower is
better. `retrieval_rate` and `citation_rate` are averages, not percentages, can
exceed 1.0, and are printed as-is.

**Visibility rising while average position falls is normal.** The brand is being
named in more answers, including ones where it places lower. Read the pair
together before calling it a regression.

### Semrush

No official MCP server at the time of writing, so this is export-driven unless
your account exposes an API you have wired up yourself.

| Need | Where it comes from | Into |
|------|--------------------|------|
| `keywords` | Keyword Magic Tool, export to CSV | Paste, or read the CSV directly |
| `serp` | Keyword Overview, the SERP panel | Paste the top 10 with date and country |
| `backlinks` | Backlink Analytics, export referring domains | Paste or read the CSV |
| `crawl` | Site Audit, export crawled pages | `python -m seo_tools crawl <export.csv>` |

Two traps when swapping from Ahrefs. Keyword Difficulty is **not** comparable
between vendors: they are different scales, so never mix them in one table or
compare this month's Semrush number to last month's Ahrefs one. And Semrush
traffic figures are a model, exactly like Ahrefs', so Search Console still wins
on what the site received.

### Anything else, including a spreadsheet

Both import commands take `--columns` to name the columns positionally, so an
export from a tool nobody here has heard of still works:

```bash
python -m seo_tools crawl export.csv --columns url,status,title,-,canonical
python -m seo_tools gsc export.csv --columns query,clicks,impressions,-,position
```

For needs with no import path, hand the data to the skill in the conversation and
say where it came from and when. The skill will use it and label it user-supplied.

## When a need has no provider

Every skill still runs. What changes:

| Need with no provider | What the skill does |
|----------------------|--------------------|
| `keywords` | Asks for an export, or works on the terms you supply and leaves volume blank |
| `serp` | Asks you to paste the top 10, with the date and the country you searched from |
| `traffic` | Says the traffic picture is unknown, and ranks on strategic value instead |
| `crawl` | Works from a sample of URLs you name, and states the sample size |
| `backlinks` | States that authority is unmeasured rather than guessing at it |
| `ai-visibility` | Run the prompts by hand, record date, engine and locale, treat as a sample of one |
| `vitals` | Flags that field data is missing and does not infer speed from the HTML |

A skill running without data says so at the top of its output, in one line, and
never fills the gap with an estimate. That rule is in
[`PRINCIPLES.md`](../PRINCIPLES.md) and it overrides any individual skill.

## Adding a provider

1. Add a row to the **Providers** table above: what it serves, how, and the cost.
2. Add a subsection under **Provider detail** with the exact tool names or export
   path, and the unit traps. The traps matter more than the tool names: a metric
   on a different scale is worse than a missing metric, because it looks usable.
3. If it can be imported as a file, check whether `seo_tools crawl` or
   `seo_tools gsc` already recognises its headers. If not, add the aliases to
   `COLUMN_ALIASES` in the matching module and a test in `tests/test_crawl.py` or
   `tests/test_locales.py`.
4. Do not edit the skills. They are written against needs, not providers, and that
   is the property worth keeping.
