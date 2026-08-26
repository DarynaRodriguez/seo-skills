# seo-skills

**The open-source skills that turn your agent into a full SEO team.**

Install once. Your agent, Claude Code, Cowork, Codex, or any agent that reads
skills, stops giving you generic SEO advice and starts doing the work: keyword
maps, content briefs, meta copy, technical triage, cannibalisation resolution,
and honest AI-answer visibility.

Not a checklist. Twenty-five skills that each do one job, hand off to each other,
and refuse to invent a number.

📋 **Copy this prompt into any AI:**

```
Install https://github.com/DarynaRodriguez/seo-skills from the GitHub repo,
then run /seo-profile-setup for my site.
```

---

## What your agent can do once this is installed

Each capability is a skill. Invoke it by name, `/meta-writer`, `/citation-gap`,
or just describe what you want and your agent picks the right one.

### 🧭 Set up, once

- **`/seo-profile-setup`** researches your site, drafts a profile, and asks you only to correct it. Every other skill reads that profile, so nothing downstream is generic.
- **`/site-inventory`** builds the baseline every audit needs: every URL with type, market, title, H1 and 28-day Search Console performance.

### 🔍 Research, decide what to target

- **`/keyword-discovery`** turns seeds, your own rankings and your Search Console queries into a classified candidate set, plus a discard list with reasons.
- **`/serp-analysis`** reads one result page like a competitor: what wins, what features eat the clicks, what the entry price is, and whether to walk away.
- **`/competitor-gap`** finds what rivals own and you do not, and separates terms to win from terms to concede.
- **`/keyword-prioritisation`** scores candidates with a formula you can see and argue with, then sequences the build against your real publishing capacity.
- **`/keyword-page-mapping`** assigns one primary keyword per page across the whole site, resolves contested terms, and names the new pages the map requires.
- **`/demand-trends`** tells you whether demand is growing, seasonal, or already gone, and catches the category-name shift that quietly breaks a content plan.

### ✍️ Optimise, produce and improve pages

- **`/content-brief`** writes the brief a writer can work from without a single follow-up question, including the angle that differentiates it from what already ranks.
- **`/meta-writer`** writes titles and descriptions that fit, in your language variant, and starts with the pages already getting impressions and losing the click.
- **`/heading-architect`** builds the H1 to H3 structure, one question per H2, and rejects headings that read as keyword shelves.
- **`/page-optimiser`** takes one live URL and returns a ranked fix list, including the verdict that the page should be merged, rewritten, or retired.
- **`/snippet-targeting`** wins the answer box, and tells you when winning it would cost you the click.
- **`/schema-builder`** produces JSON-LD that describes what is actually on the page. No fake FAQs, no invented reviews.
- **`/internal-linking`** finds the orphans, the buried anchors, and the authority sitting on a page that links to nothing.

### 🩺 Audit, find and rank what is broken

- **`/technical-audit`** triages technical health by traffic at risk, not by issue count, and returns six fixes instead of three hundred rows.
- **`/cannibalisation-audit`** proves two pages are competing with position history, then names which one should win and why.
- **`/content-decay`** separates real decay from seasonality, dead demand, and a SERP layout change, then decides refresh, consolidate, or retire.
- **`/indexation-check`** answers both halves of the question: what should be indexed and is not, and what is indexed and should not be.
- **`/performance-report`** writes the monthly report you can send to a CMO unedited, brand split from non-brand, with an honest caveats section.

### 🤖 AI visibility, get cited by the answer engines

- **`/ai-crawler-access`** checks the prerequisite nobody checks: whether the fetchers can reach your pages at all. Run this before anything else in this lane.
- **`/ai-visibility-audit`** gives the honest baseline: visibility, share of voice, sentiment and position, aided and unaided kept separate.
- **`/citation-gap`** finds which sources the engines cite for your buyer's questions, and sorts the fix into owned, editorial, reference, and community, because a G2 listing is not a content problem.
- **`/geo-rewrite`** makes a page quotable without turning it into robot food, and says what no rewrite can fix.
- **`/prompt-panel`** builds the tracked prompt set from real buyer evidence, and refuses the industry's favourite trick of adding branded prompts to lift the average.

---

## Three workflows to start with

**New site, nothing set up.**

```
/seo-profile-setup  →  /site-inventory  →  /keyword-discovery  →
/keyword-prioritisation  →  /keyword-page-mapping
```

**Organic traffic is down and nobody knows why.**

```
/performance-report  →  /technical-audit  →  /indexation-check  →
/content-decay  →  /cannibalisation-audit
```

**We are invisible in ChatGPT and Perplexity.**

```
/ai-crawler-access  →  /prompt-panel  →  /ai-visibility-audit  →
/citation-gap  →  /geo-rewrite
```

More in [`docs/workflows.md`](docs/workflows.md).

---

## The profile is the whole trick

Generic SEO advice is worthless because it does not know your market, your buyer,
your competitors, or the words your legal team has banned. So the first skill you
run writes a profile, and every other skill reads it.

`/seo-profile-setup` researches your site first and hands you a draft to correct,
rather than an empty form. The output lands in `.seo/profile.md` (per project) or
`~/.seo-skills/profile.md` (everywhere), and covers markets and language variants,
buyer and job to be done, product vocabulary, banned words, competitors, site
structure, this quarter's one metric, and which answer engines matter.

Schema and a fully commented example: [`profiles/PROFILE.template.md`](profiles/PROFILE.template.md).
A filled-in worked example: [`profiles/example-b2b-saas.md`](profiles/example-b2b-saas.md).

---

## Live data, or honest blanks

The skills run on real data when a connector is there, and say so plainly when it
is not. Two are wired in by default:

- **Ahrefs MCP** for keywords, SERPs, Search Console, site audit, backlinks and Brand Radar.
- **Peec AI MCP** for AI-answer visibility, citations and crawler hits.

With neither, every skill still runs. It asks for an export, works from the pages
themselves, and writes "no volume data available for these 12 terms" instead of
filling the column with a guess. Tool names and unit gotchas live in
[`docs/data-sources.md`](docs/data-sources.md).

---

## What runs where

| Skill | Claude.ai & Cowork | Claude Code & local agents | ChatGPT Work | ChatGPT |
|-------|:---:|:---:|:---:|:---:|
| **Set up** | | | | |
| seo-profile-setup | ⚠️ | ✅ | ⚠️ | ⚠️ |
| site-inventory | 🔧 | 🔧 | 🔧 | ⚠️ |
| **Research** | | | | |
| keyword-discovery | 🔧 | 🔧 | 🔧 | ⚠️ |
| serp-analysis | 🔧 | 🔧 | 🔧 | ⚠️ |
| competitor-gap | 🔧 | 🔧 | 🔧 | ⚠️ |
| keyword-prioritisation | ✅ | ✅ | ✅ | ⚠️ |
| keyword-page-mapping | ✅ | ✅ | ✅ | ⚠️ |
| demand-trends | 🔧 | 🔧 | 🔧 | ⚠️ |
| **Optimise** | | | | |
| content-brief | ✅ | ✅ | ✅ | ⚠️ |
| meta-writer | ✅ | ✅ | ✅ | ⚠️ |
| heading-architect | ✅ | ✅ | ✅ | ⚠️ |
| page-optimiser | ✅ | ✅ | ✅ | ⚠️ |
| snippet-targeting | ✅ | ✅ | ✅ | ⚠️ |
| schema-builder | ✅ | ✅ | ✅ | ⚠️ |
| internal-linking | 🔧 | 🔧 | 🔧 | ⚠️ |
| **Audit** | | | | |
| technical-audit | 🔧 | 🔧 | 🔧 | ⚠️ |
| cannibalisation-audit | 🔧 | 🔧 | 🔧 | ⚠️ |
| content-decay | 🔧 | 🔧 | 🔧 | ⚠️ |
| indexation-check | 🔧 | 🔧 | 🔧 | ⚠️ |
| performance-report | 🔧 | 🔧 | 🔧 | ⚠️ |
| **AI visibility** | | | | |
| ai-crawler-access | ⚠️ | ✅ | ⚠️ | ⚠️ |
| ai-visibility-audit | 🔧 | 🔧 | 🔧 | ⚠️ |
| citation-gap | 🔧 | 🔧 | 🔧 | ⚠️ |
| geo-rewrite | ✅ | ✅ | ✅ | ⚠️ |
| prompt-panel | ✅ | ✅ | ✅ | ⚠️ |

**Legend**

- ✅ **Runs out of the box.** No setup, works anywhere your agent does.
- 🔧 **Better with a connector.** Runs without Ahrefs or Peec, but asks you for an export and leaves data columns blank rather than estimating them.
- ⚠️ **Limited.** Runs as a one-shot pass with nothing saved between sessions: no stored profile, no `.seo/` working files, no crawl. Consumer ChatGPT is limited across the board because Skills are not available on consumer accounts.

---

## Install

### Claude.ai and Cowork

1. Open **Customize**.
2. Go to **Personal plugins**.
3. Click **Create plugin**, then **Add marketplace**, then **Add from a repository**.
4. Enter `DarynaRodriguez/seo-skills` and confirm.
5. Open the new marketplace, find `seo-skills`, and click **Install**.

Then connect **Ahrefs** and **Peec AI** as MCP connectors if you have accounts.
Both are optional.

### Claude Code and other local agents

```bash
git clone https://github.com/DarynaRodriguez/seo-skills.git
cd seo-skills
./install.sh
```

`install.sh` detects your agent and copies the skills into place:
`~/.claude/skills/` for Claude Code, `~/.codex/skills/` for Codex, or a directory
you name. Pass `--target <dir>` to override, `--link` to symlink instead of copy
so `git pull` updates the skills in place.

### ChatGPT Work

Skills are supported on Work accounts. Upload the `skills/` directory contents,
or point the workspace at this repo. Consumer ChatGPT has no Skills support, so
paste an individual `SKILL.md` into the conversation instead.

---

## What gets installed

```
skills/
├── seo-profile-setup/SKILL.md          the interview that writes .seo/profile.md
├── site-inventory/SKILL.md             the page baseline every audit reads
├── keyword-discovery/SKILL.md
├── serp-analysis/SKILL.md
├── ... 21 more
└── schema-builder/
    ├── SKILL.md
    └── references/schema-recipes.md    copy-paste JSON-LD per page type
```

Working files the skills create in your project, all plain text and all yours:

```
.seo/
├── profile.md              your site, markets, buyer, banned words
├── pages.csv               the page inventory
├── keyword-candidates.csv
├── keyword-map.csv         one primary keyword per page
└── keyword-priorities.csv  the sequenced build order
```

---

## The rules these skills follow

Read [`PRINCIPLES.md`](PRINCIPLES.md) before you trust any SEO tool, this one
included. The short version:

- **Never invent a metric.** Every number carries its source and its date. A missing connector is a stated limitation, not a licence to estimate.
- **Never promise a ranking, a citation, or a date for one.** Nobody controls search results or AI answers.
- **No black hat.** No cloaking, bought links, doorway pages, spun content, or schema describing something the page does not contain.
- **Changing the tracked prompt set is not a way to improve AI visibility.** It changes coverage, not performance. Aided and unaided prompts are never blended.
- **A named human approves every publish.** Skills draft, audit, and recommend.

---

## Contributing

New skills, better procedures, corrections to the data-source mappings: all
welcome. [`docs/skill-template.md`](docs/skill-template.md) is the required shape,
[`CONTRIBUTING.md`](CONTRIBUTING.md) has the rest. One rule that trips people up:
no em dashes anywhere in the repo, because half the skills teach a house style
that bans them and the repo should practise what it teaches.

## Licence

MIT. See [`LICENSE`](LICENSE).
