# Getting started

For agents. If you are a human, the README is friendlier.

## The contract

Twenty-seven skills in `skills/`, each a `SKILL.md` with frontmatter. They share
three things:

1. **A profile.** `.seo/profile.md` in the working project, or
   `~/.seo-skills/profile.md` globally. Every skill reads it at Step 0. It holds
   the site, markets, language variants, buyer, competitors, product vocabulary,
   banned words, site structure, this quarter's metric, and the answer engines that
   matter. Without it, output is generic, which is the failure mode this repo
   exists to prevent.
2. **Working files.** Skills read and write plain CSV and markdown in `.seo/`:
   `pages.csv`, `keyword-candidates.csv`, `keyword-map.csv`,
   `keyword-priorities.csv`. They are the handoff format between skills.
3. **`PRINCIPLES.md`.** Overrides any individual skill. Read it once.

## First run

```
1. /seo-profile-setup      research the site, draft a profile, confirm it
2. /site-inventory         build .seo/pages.csv
3. pick a lane             docs/workflows.md has the chains
```

If no profile exists and the user wants work done now, gather the six essentials
inline (domain, markets and languages, buyer, competitors, product vocabulary,
banned words), do the job, then offer to run `/seo-profile-setup` so the next run
is cheaper. Do not invent profile values.

## Data

Optional connectors: **Ahrefs MCP** (keywords, SERPs, Search Console, site audit,
backlinks, Brand Radar) and **Peec AI MCP** (AI-answer visibility, citations,
crawler hits). Tool names, unit conventions, and the fallback for every data need
are in [`data-sources.md`](data-sources.md).

Two unit traps worth memorising: Ahrefs money values are USD cents, and Peec
`visibility`, `share_of_voice` and `retrieved_percentage` are 0 to 1 ratios while
`retrieval_rate` and `citation_rate` are averages that can exceed 1.0 and print
as-is.

With no connectors every skill still runs, asks for an export, and leaves data
columns blank rather than filling them with an estimate.

## Choosing a skill

Match the request to one skill, not several. If a request spans lanes, say which
chain you are running and run it in order. The frontmatter `when_to_use` field is
the routing signal, and it names the skills that typically hand off to each one.

Requests that look like one skill but are not:

| Request | Skill |
|---------|-------|
| "Why is traffic down" | `/performance-report` first, then diagnose |
| "Optimise this page for AI" | `/ai-crawler-access` before `/geo-rewrite` |
| "Should we write about X" | `/serp-analysis`, then `/keyword-prioritisation` |
| "Two pages rank for the same thing" | `/cannibalisation-audit`, not `/keyword-page-mapping` |
| "Improve our AI visibility score" | `/ai-visibility-audit`, and say that changing the prompt set is not an improvement |

## Editing skills

See [`skill-template.md`](skill-template.md) for the required shape and
[`../AGENTS.md`](../AGENTS.md) for the repo rules. Validate with
`python3 scripts/validate.py`, then `./scripts/sync-plugin.sh`.
