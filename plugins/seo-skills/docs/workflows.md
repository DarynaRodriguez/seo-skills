# Workflows

Each skill does one job. Real work is a chain. These are the chains that come up
most, with the reason each step comes where it does.

## 1. New site, nothing set up

```
/seo-profile-setup  →  /site-inventory  →  /keyword-discovery  →
/serp-analysis (per shortlisted term)  →  /keyword-prioritisation  →
/keyword-page-mapping
```

Why this order: the profile makes everything downstream specific. The inventory
tells you what already exists, which is usually more than the team remembers.
Discovery before prioritisation, because you cannot rank a list you have not
built. `/serp-analysis` sits before prioritisation deliberately: a term with a
SERP full of listicles is not a candidate for a product page at any volume.

Output after this chain: `.seo/profile.md`, `.seo/pages.csv`,
`.seo/keyword-candidates.csv`, `.seo/keyword-priorities.csv`,
`.seo/keyword-map.csv`. That is the working set every other skill reads.

## 2. Traffic is down and nobody knows why

```
/performance-report  →  /drift-check  →  /technical-audit  →
/indexation-check  →  /content-decay  →  /cannibalisation-audit
```

Why this order: quantify before diagnosing. Rule out the site-wide causes
(something broke, pages fell out of the index) before the page-level ones (content
aged, pages started competing). Running `/content-decay` first on a site that
quietly noindexed a template wastes a week.

`/drift-check` goes second when there is a baseline to diff against, because
"what changed on this page since 12 August" is a cheaper question than "what is
wrong with this site", and it usually names the cause outright. With no baseline
it has nothing to say: skip it, and take one now so the next drop is covered.

Split brand from non-brand early. A drop that is entirely brand queries is a
marketing spend story, not an SEO one, and `/performance-report` separates them.

## 3. We are invisible in ChatGPT and Perplexity

```
/ai-crawler-access  →  /prompt-panel  →  /ai-visibility-audit  →
/citation-gap  →  /geo-rewrite
```

Why this order: `/ai-crawler-access` first, always. Rewriting pages that a fetcher
cannot retrieve is wasted work, and blocked-by-WAF is a more common cause of zero
visibility than bad content. Then define what you measure, then measure it, then
find who gets cited instead of you, then fix the pages.

Expect `/citation-gap` to send half the work outside your site. A competitor cited
from a review-site roundup is a listings problem. That is a real finding, not a
failure of the chain.

## 4. One page, and it will not rank

```
/serp-analysis  →  /page-optimiser  →  /meta-writer  →
/heading-architect  →  /internal-linking
```

Why this order: read the SERP before touching the page, because the most common
cause of a page not ranking is intent mismatch, which no amount of on-page work
fixes. `/internal-linking` last, because a page nobody links to will not rank
however good it is, and that is easier to see once the page itself is sound.

## 5. Commissioning new content

```
/keyword-page-mapping  →  /serp-analysis  →  /content-brief  →
/heading-architect  →  /snippet-targeting  →  /schema-builder  →  /meta-writer
```

Why this order: the map prevents you from commissioning a page that competes with
one you already own. Brief before outline, outline before snippet blocks, schema
last because it describes what the finished page actually contains.

## 6. Shipping a redesign, migration or template change

```
/drift-check baseline  →  ship  →  /drift-check  →  /technical-audit
```

The only workflow in this pack that has to start before the work does. Baseline
the ten to thirty pages carrying real clicks, ship, then diff. A canonical that
moved or a `noindex` that appeared shows up in seconds instead of surfacing six
weeks later as an unexplained decline.

Two failure modes to name out loud. Baselining four hundred pages produces a
report nobody reads. And a baseline taken while the site was mid-deploy is a
false known-good, so check the status in the snapshot before trusting it.

If content moved client side during the change, that is the finding to escalate:
it still looks right in a browser while anything that does not run JavaScript
sees an empty page. Hand it to `/ai-crawler-access`.

## 7. Monthly rhythm

| Cadence | Run |
|---------|-----|
| Weekly | `/meta-writer` on the CTR laggards, `/page-optimiser` on one priority page |
| Monthly | `/performance-report`, `/content-decay`, `/ai-visibility-audit` |
| Quarterly | `/technical-audit`, `/cannibalisation-audit`, `/indexation-check`, `/competitor-gap`, `/keyword-prioritisation` to re-sequence |
| When the market moves | `/demand-trends`, `/prompt-panel` to add newly real buyer questions |
| Once, then when the business changes | `/seo-profile-setup`, `/site-inventory` |

## Chaining rules

**Hand off the artefact, not the summary.** Skills read `.seo/*.csv` files. Passing
a chat summary of a keyword map loses the columns the next skill needs.

**Re-run the profile when the business changes.** A new market, a new buyer, a
renamed product, a legal restriction on a claim: any of these invalidates output
from every skill downstream.

**Stop when a skill says stop.** `/serp-analysis` returning "leave it" and
`/page-optimiser` returning "retire this page" are results. Do not run the next
skill in the chain to get a different answer.
