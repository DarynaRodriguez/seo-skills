# Data sources

The skills are written to run on live data when it is there, and to degrade
honestly when it is not. This file is the single place tool names live, so a skill
never hardcodes a guess.

Two connectors are wired in by default: **Ahrefs** (search data, Search Console,
site audit, backlinks, Brand Radar) and **Peec AI** (AI-answer visibility). Both
are optional. Every skill states what it does without them.

Tool names below are the MCP tool identifiers as exposed by the official Ahrefs
and Peec AI MCP servers. If your agent surfaces them under different names, the
mapping is the only thing you need to change.

## Ahrefs

### Keywords

| Job | Tool |
|-----|------|
| Volume, difficulty, CPC, intent for known terms | `mcp__Ahrefs__keywords-explorer-overview` |
| Expand a seed by phrase match | `mcp__Ahrefs__keywords-explorer-matching-terms` |
| Semantically related terms | `mcp__Ahrefs__keywords-explorer-related-terms` |
| Autocomplete-style long tail | `mcp__Ahrefs__keywords-explorer-search-suggestions` |
| Which country the demand sits in | `mcp__Ahrefs__keywords-explorer-volume-by-country` |
| Seasonality and trend | `mcp__Ahrefs__keywords-explorer-volume-history` |

### SERP and competitors

| Job | Tool |
|-----|------|
| Who ranks now, with features | `mcp__Ahrefs__serp-overview` |
| Domains competing for the same keywords | `mcp__Ahrefs__site-explorer-organic-competitors` |
| A domain's ranking keywords | `mcp__Ahrefs__site-explorer-organic-keywords` |
| A domain's best pages | `mcp__Ahrefs__site-explorer-top-pages`, `mcp__Ahrefs__site-explorer-pages-by-traffic` |
| Many domains at once | `mcp__Ahrefs__batch-analysis` |
| Tracked-keyword positions | `mcp__Ahrefs__rank-tracker-overview`, `mcp__Ahrefs__rank-tracker-serp-overview` |

### Search Console

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

### Site audit and crawl

| Job | Tool |
|-----|------|
| Which audit projects exist | `mcp__Ahrefs__site-audit-projects` |
| Issue list by severity | `mcp__Ahrefs__site-audit-issues` |
| Per-URL crawl detail | `mcp__Ahrefs__site-audit-page-explorer` |
| Rendered content of one page | `mcp__Ahrefs__site-audit-page-content` |
| Pages Ahrefs has seen | `mcp__Ahrefs__site-explorer-crawled-pages` |
| Internal link counts | `mcp__Ahrefs__site-explorer-pages-by-internal-links`, `mcp__Ahrefs__site-explorer-linked-anchors-internal` |

### Links

| Job | Tool |
|-----|------|
| Domain Rating, now and over time | `mcp__Ahrefs__site-explorer-domain-rating`, `mcp__Ahrefs__site-explorer-domain-rating-history` |
| Backlink and referring-domain totals | `mcp__Ahrefs__site-explorer-backlinks-stats`, `mcp__Ahrefs__site-explorer-referring-domains` |
| Individual links | `mcp__Ahrefs__site-explorer-all-backlinks` |
| Links pointing at dead URLs | `mcp__Ahrefs__site-explorer-broken-backlinks` |
| Anchor-text distribution | `mcp__Ahrefs__site-explorer-anchors` |

### AI answers (Ahrefs Brand Radar)

| Job | Tool |
|-----|------|
| How often a brand appears in AI answers | `mcp__Ahrefs__brand-radar-mentions-overview`, `-mentions-history` |
| Share of voice | `mcp__Ahrefs__brand-radar-sov-overview`, `-sov-history` |
| Which domains and pages get cited | `mcp__Ahrefs__brand-radar-cited-domains`, `mcp__Ahrefs__brand-radar-cited-pages` |
| The raw AI answers | `mcp__Ahrefs__brand-radar-ai-responses` |
| Tracked prompts | `mcp__Ahrefs__management-brand-radar-prompts` |

### Housekeeping

`mcp__Ahrefs__doc` before first use of an unfamiliar endpoint.
`mcp__Ahrefs__management-projects`, `-project-keywords`, `-locations` to resolve
project and location IDs. `mcp__Ahrefs__subscription-info-limits-and-usage` before
a large pull, so a run does not burn a month of units.

**Units.** Every monetary value (`value`, `org_cost`, `paid_cost`, `traffic_value`)
is in USD cents. Divide by 100 before display.

**Rendering.** When a response carries `render_with` in its metadata, call that
render tool (`render-data-table`, `render-scorecard`, `render-time-series-chart`)
rather than dumping the raw rows.

## Peec AI

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

## No connectors at all

Every skill still runs. What changes:

| Instead of | Do this |
|-----------|---------|
| Volume and difficulty | Ask for a Keyword Planner, Ahrefs or Semrush export as CSV, and label all figures as user-supplied |
| SERP data | Ask the user to paste the top 10 for the query, with the date and the country they searched from |
| Search Console | Ask for a Search Console export, or run on page content alone and say the traffic picture is unknown |
| Site audit | Read the pages directly with a fetch tool, or ask for a Screaming Frog export |
| AI visibility | Run the prompts by hand in the target engines, record date, engine, and locale, and treat the result as a sample of one |

A skill that runs without data says so at the top of its output, in one line, and
never fills the gap with an estimate.
