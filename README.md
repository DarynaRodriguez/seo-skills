# seo-skills

**The open-source skills that turn your agent into a full SEO team.**

Install once. Your agent, Claude Code, Cowork, Codex, or any agent that reads
skills, stops giving you generic SEO advice and starts doing the work: keyword
maps, content briefs, meta copy, technical triage, cannibalisation resolution,
and honest AI-answer visibility.

Not a checklist. Twenty-seven skills that each do one job, hand off to each other,
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
- **`/drift-check`** snapshots a page before you ship and tells you exactly what changed after, classified by whether anyone would have done it on purpose.
- **`/site-audit`** audits a whole site by running specialist agents in parallel, one per page, then ranks every finding by the clicks it puts at risk.

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
/performance-report  →  /drift-check  →  /technical-audit  →
/indexation-check  →  /content-decay  →  /cannibalisation-audit
```

`/drift-check` goes second because "what changed" is cheaper to answer than
"what is wrong", and it only works if you took a snapshot beforehand.

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

## Bring your own data

There is no version of this that produces good output from nothing. Every skill
answers a question that needs evidence, so plugging in data is the setup step, not
an optional upgrade.

What is optional is **which tool**. The skills are written against 12 named data
needs, and each need can be served by whatever you already pay for:

| Need | Served by |
|------|-----------|
| Page content, robots, sitemaps | **this repo, free, no account** |
| Crawl | **Screaming Frog**, Sitebulb, Semrush, Ahrefs, or any CSV |
| Traffic | **Search Console export**, free, or Ahrefs |
| Keywords, SERPs, backlinks | Ahrefs, Semrush, or a paste |
| AI visibility and citations | Peec AI, Ahrefs Brand Radar, or by hand |

Declare yours in profile section 11 and the skills follow it. Switching from
Ahrefs to Semrush is a line in a profile, not a rewrite.

The stack this pack is written against is Search Console, Ahrefs and Peec AI, and
[`docs/data-sources.md`](docs/data-sources.md) says why without pretending the
alternatives produce worse output. It also carries the traps that bite when
switching: Keyword Difficulty is not comparable between vendors, and every
vendor's traffic figure is a model while Search Console is what you received.

Where a need has no provider, the skill says so in one line and never fills the
gap with an estimate.

---

## Measured, not guessed

A skill written only as prose has to ask a model to read a page and report what
the title is. That works most of the time, which is exactly the problem: the
failures are invisible and nothing can be re-checked.

So the facts come from tools instead. `seo_tools` is a small command line layer
that measures the things a skill should never estimate, and every skill that has
a tool behind it calls it rather than eyeballing the page.

```bash
python -m seo_tools doctor            # will this run on my machine
python -m seo_tools page <url>        # everything measurable on one page
python -m seo_tools meta <url>        # does the title fit, in pixels
python -m seo_tools robots <url>      # which AI crawlers may read this
python -m seo_tools gsc export.csv    # what your Search Console export says
```

**No install.** Standard library Python only, so it runs with whatever Python is
already on your machine. No `pip install`, no requirements file, no API key, no
account. CI fails the build if a dependency file ever appears.

**Testable, which is the point.** 140 tests, run with
`python -m unittest discover -s tests -t .` and no test runner to install.
Writing them found five real bugs, including a robots.txt group-precedence case
that would have reported GPTBot as allowed when it was blocked.

Three things worth knowing:

- **`robots` separates blocked crawlers by what blocking them costs.** A blocked
  live-fetch or search-index crawler costs you citations now. A blocked training
  crawler costs you nothing today. Blocking `Google-Extended` does not remove
  you from Google Search or AI Overviews, and there is a test pinning that.
- **`meta` measures pixels, not characters.** "Illinois" and "Wholesale" are both
  nine characters and one is nearly twice as wide. The number is labelled an
  estimate in the output, with the method, every time.
- **`baseline` and `drift` give the pack a memory.** Snapshot a page, ship, then
  ask what changed. 19 rules, fixed severities, and the rule that fired is named
  so you can disagree with it.

`gsc` is the one to try first if you have no paid tools: a Search Console CSV
export is free, is real received traffic rather than a model of it, and drives
the cannibalisation, decay and prioritisation work.

Full reference, including the deliberate limits and how to use it from ChatGPT:
[`docs/execution-layer.md`](docs/execution-layer.md).

---

## Agents, for the work that is too big for one pass

A site audit is not one job. It is the same job on thirty pages, and doing it
sequentially is why site audits get abandoned half finished.

So `/site-audit` does not audit anything itself. It fans out four specialists,
each in its own context, each writing findings to a file so the results survive
the fan-out and can be put back together:

| Agent | Runs | Answers |
|-------|------|---------|
| `seo-crawl-analyst` | once, first | The site-level findings, and which pages are worth auditing individually |
| `seo-ai-access-checker` | once per market | Can the AI and search crawlers reach these pages, and is the content in the served HTML |
| `seo-page-auditor` | once per URL, concurrently | Everything measurable on one page |
| `seo-drift-watcher` | once per baselined URL | What changed since the snapshot |

A fifth runs on the other side of the work. Once an audit has said what is wrong,
`/content-brief` fans out `seo-brief-writer`, one instance per page, to say what
should be written instead. It answers with one of `write`, `rewrite`, `merge` or
`do_not_publish`, and the last of those is the point: an agent that can only say
yes is a content mill with a schema.

The orchestrator then aggregates by finding rather than by page, so one template
problem across thirty URLs is one row and not thirty, and ranks by clicks at risk
rather than by severity. Ten rows out, the rest counted in a line.

Two rules make it usable rather than impressive. The crawl analyst runs alone and
first, because the page set is its output and a guessed page set wastes every
agent after it. And the page set is capped: ten to thirty URLs, chosen by traffic
and by finding. If it grows past fifty, the narrowing failed and the fix is to go
back, not to launch a hundred agents.

Agents live in `agents/`. They install alongside the skills, and
`scripts/validate.py` checks their frontmatter, their model names, and that every
tool command they reference actually exists.

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
| drift-check | ⚠️ | ✅ | ⚠️ | ⚠️ |
| site-audit | ⚠️ | ✅ | ⚠️ | ⚠️ |
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
you name. It also installs the tool layer next to them, because a skill that
tells you to run a command you do not have is worse than no skill. The installer
prints the exact path, and the first thing to run is:

```bash
python ~/.claude/seo-skills-tools/seo.py doctor
```

Flags: `--target <dir>` to choose the location, `--link` to symlink instead of
copy so `git pull` updates everything in place, `--list` to preview, and
`--skills-only` if you genuinely want the prose without the tools.

### ChatGPT Work

Skills are supported on Work accounts. Upload the `skills/` directory contents,
or point the workspace at this repo. Consumer ChatGPT has no Skills support, so
paste an individual `SKILL.md` into the conversation instead.

The tool layer needs somewhere to run shell commands, which browser ChatGPT does
not have. Two options: run the commands on your own machine and paste the
`--json` output in, or use Codex, which reads `AGENTS.md` and runs them directly.
`gsc` is the exception and works anywhere, because it reads a file you upload
rather than the network. Details in
[`docs/execution-layer.md`](docs/execution-layer.md).

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
