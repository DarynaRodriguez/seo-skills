# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] 2026-08-27

### Added

Subagents, so a whole-site audit runs in parallel instead of page by page.

- **`/site-audit`**, the twenty-seventh skill and the first orchestrator here. It
  audits nothing itself: it fans out four specialists, reads the files they write,
  aggregates by finding rather than by page so one template problem across thirty
  URLs is one row, and ranks by clicks at risk rather than by severity. Ten rows
  out, the rest counted in a line.
- **`agents/`** with four subagents, each carrying a persistence contract so the
  fan-out can be put back together: `seo-crawl-analyst` (runs first and alone,
  because the page set is its output), `seo-ai-access-checker` (one per market),
  `seo-page-auditor` (one per URL, concurrently) and `seo-drift-watcher` (one per
  baselined URL).
- `scripts/validate.py` now checks agent frontmatter against the Claude Code
  subagent reference: required fields, unknown keys, model names, tool names, and
  that every `python -m seo_tools` command an agent references exists. Verified by
  breaking each rule on purpose and watching it fail.
- Agents ship in the plugin mirror and via `install.sh`, and CI asserts the mirror
  carries skills, agents and tools. A plugin with `/site-audit` and no agents
  would be a skill that cannot run, which is the defect the tool layer already had
  once.
- `docs/data-sources.md` gains the `crawl` command reference, and
  `docs/execution-layer.md` documents it properly.

### Fixed

- **Cyrillic, Greek and Hebrew were measured at a default width.** Every glyph in
  those scripts fell through to 556 units. Cyrillic Sha is 917, so a Russian title
  was under-measured by up to 65% per wide character. Now measured from real font
  metrics extracted by `scripts/extract_font_widths.py`, which parses the font
  directly rather than trusting a transcription.
- **The German sharp s was wrong.** Recorded as 556, the font says 611. Found by
  running the new extractor with `--verify` against the hand-written table, which
  now passes clean over all 117 entries.
- **Arabic and Indic widths were silently wrong rather than absent.** Arabic is
  cursive, so letters join and change form and an isolated codepoint's advance is
  not what renders. The Indic scripts form conjuncts, and Arial contains no
  Devanagari at all. Both now report `UNRELIABLE` in the `method` field, label the
  width a floor rather than an estimate, and emit `title.width_unmeasurable`
  instead of a truncation verdict. A pass or fail on a number that does not mean
  what it looks like is worse than no verdict.
- **CI derived its smoke-test command list from a hardcoded string**, and it had
  already fallen behind: `crawl` shipped without being smoke tested. Read off the
  parser now, so a new command cannot skip it.

### Added

Data providers are now swappable. You still cannot do this work without data, and
the pack says so plainly, but which tool supplies it is your choice.

- **`seo_tools crawl`**, a thirteenth command that reads a crawl export from
  Screaming Frog, Sitebulb, Semrush Site Audit, Ahrefs Site Audit or a
  hand-built spreadsheet, and normalises all of them onto one row shape. Every
  analysis reads that shape, so adding an exporter means adding column aliases
  rather than code. Answers on its own, with no API and no network: status
  distribution, broken URLs ordered by inlinks so severity is visible, redirect
  chains, duplicate titles, descriptions and H1s, missing fields, canonicals
  pointing elsewhere, orphans, and thin pages against a threshold you pass.
  Duplicates and missing-field counts deliberately ignore non-indexable pages,
  because a duplicate title on a noindexed thank-you page competes with nothing.
- `docs/data-sources.md` rewritten around **12 data needs** rather than two
  vendors. Each need lists which skills use it and which providers serve it,
  including Semrush, Screaming Frog, Sitebulb, Search Console and a plain CSV.
  Says which stack the pack is written against and why, without pretending the
  alternatives are worse, and carries the traps that matter when switching, such
  as Keyword Difficulty not being comparable between vendors.
- Profile section 11, **Data providers**, where you name what serves each need.
  Skills read it at Step 0. Writing `none` is a supported answer and a better one
  than naming a tool you do not have, because it makes the skill report a gap.
- All 26 skills: the Data table column is now "Our stack" rather than "Live
  tool", and each table carries a note that the middle column is swappable. Six
  skills gained the `crawl` command in their Tools table.
- `--columns` on `crawl`, matching the flag on `gsc`, so an exporter nobody has
  heard of still works: `--columns url,status,title,-,canonical`.
- 25 tests for the crawl layer, including one class asserting that two different
  exporters describing the same defect produce the same finding.

### Fixed

- `ci`: bumped `actions/checkout` to v7 and `actions/setup-python` to v7. Both
  targeted the deprecated Node 20 runner.

## [0.3.0] 2026-08-27

### Fixed

Locale bugs. The tools handled English and German, which made them look general
while they produced wrong numbers or no numbers at all for everything else. Each
fix has a test pinning it, in `tests/test_locales.py`.

- **Word counts returned 1 for any Chinese or Japanese text.** Those scripts do
  not separate words with spaces, so counting letter runs treated a whole sentence
  as one word. Worse than a wrong count: the client-rendering heuristic is "app
  root element plus almost no text", so every CJK page was flagged as
  client-rendered. Now counted per character, with `word_count_basis` reporting
  which rule applied. Korean is unaffected, since it uses spaces.
- **Title and description widths measured wide characters as Latin ones.** A CJK
  title that truncates reported as fitting, in the pack's flagship deterministic
  feature. Wide and fullwidth characters are now measured at one em via
  `unicodedata.east_asian_width`, and combining marks at zero so accented and
  Indic text is not charged twice for one glyph.
- **The truncation preview returned a bare ellipsis for text without spaces.**
  Cutting on word boundaries alone cannot work where there are none. Falls back to
  cutting per character.
- **Length checks used character floors, which are not comparable across scripts.**
  A 28-character Japanese title filling 85% of the available width was reported as
  too short. Every pass or fail decision is now made in pixels; character counts
  are still reported, because that is what briefs are written against.
- **Search Console exports in most languages lost their columns.** The header
  normaliser stripped every non-ASCII character, so Japanese, Korean, Chinese and
  Cyrillic headers reduced to an empty string, and Spanish, Italian, Dutch and
  Polish had no aliases. Only "CTR" matched, because it is spelled the same
  everywhere. Aliases now cover 14 languages, with `--columns` as a positional
  override for any locale not listed.
- **The crawler list covered only Western engines.** Added YandexBot, Baiduspider,
  Yeti, SeznamBot, PetalBot and Applebot, each with what blocking it costs in its
  market. Applebot is distinguished from Applebot-Extended, which is the same trap
  as Google-Extended.
- **`install.sh` installed 26 skills that call a tool layer it did not install.**
  Every measured command in every skill failed with "No module named seo_tools"
  straight after a clean install. The installer now places `seo_tools` and
  `seo.py` beside the skills, prints the exact command to run, and offers
  `--skills-only` for anyone who genuinely wants the prose alone.

### Added

Evidence from a verified AEO research pack, folded into six skills. Every figure
below was re-fetched from its primary source on 27 August 2026 before being
written in, and each carries its sample size and date in the skill text.

- `geo-rewrite`: a procedure for closing the information gaps a wrong answer
  fills. Ahrefs planted three contradicting accounts of an invented brand and put
  56 false-premise questions to eight platforms; five of the eight trusted the
  planted sources over the brand's own FAQ, while ChatGPT stayed under 7% and
  cited the official FAQ in 84% of answers. The mechanism is that a vague page
  loses to a specific fiction, so the fix is specificity: numbers, dates, named
  standards and named systems. Two guardrails added, including one against
  inventing the specifics that close the gap.
- `citation-gap`: the correlation that justifies the skill. Branded web mentions
  correlate 0.664 with AI Overview visibility against 0.218 for backlinks, 0.326
  for domain rating and 0.295 for referring domains, across 75,000 brands. Carried
  with both caveats: it is rank correlation, and the sample was filtered to
  domains above DR 40. Plus a step on unlinked mentions, which are about 72% of
  brand appearances and were previously scored as failures.
- `ai-visibility-audit`: the ranking-independence figure. Of pages AI Overviews
  cite, 37.9% rank in the top 10, 31.2% at 11 to 100, and 31.0% not in the top 100
  at all, so roughly a third of citations go to pages that do not rank.
- `keyword-discovery`: a guardrail against building a candidate set from AI
  fan-out queries. An assistant expands one prompt into roughly nine to eleven
  subqueries and about 95% have no measured volume, so they are a topic signal and
  not a keyword list.
- `keyword-prioritisation`: a click test applied before scoring. AI Overviews
  appear on 57.9% of question queries against 15.5% of non-question queries, and
  99.9% of triggering keywords carry an informational label, so absorption risk
  sits on the informational end. Candidates are now labelled `click`, `citation`
  or `both`, which changes the metric promised rather than the score.
- `performance-report`: the caveat that has to accompany any answer-engine
  referral number, because the number is always an undercount. Names the platforms
  that pass no referrer, the larger loss to direct and branded organic, and
  self-reported attribution as the only instrument that reaches revenue.

## [0.2.0] 2026-08-26

The execution layer. The skills now measure with tools instead of asking a model
to read a page and report what it saw.

### Added

- **`drift-check`**, the twenty-sixth skill and the home for baselines. Snapshot
  a page before a release, diff after, and get the changes classified by whether
  anyone would plausibly have made them on purpose. Slots into the traffic-drop
  workflow second, because "what changed" is a cheaper question than "what is
  wrong", and into a new release workflow that has to start before the work does.
- `argument-hint` on all 26 skills, so the `/` menu says whether a skill wants a
  URL, a keyword or a CSV export.
- `docs/frontmatter.md`: what each frontmatter field does, why `user-invocable`
  and `disable-model-invocation` are deliberately absent, and which distribution
  paths accept which fields.
- `scripts/validate.py` now rejects any frontmatter key outside a known set. An
  unrecognised key is ignored silently, so a misspelled `when_to_use` costs a
  skill its trigger phrases and nothing says so.
- `seo_tools`, a standard library only command line layer. No `pip install`, no
  requirements file, no API key, no account. Twelve commands: `doctor`, `fetch`,
  `page`, `meta`, `headings`, `schema`, `robots`, `sitemap`, `baseline`, `drift`,
  `history`, `gsc`. Every one takes `--json`, which is how the skills call it.
- Pixel measurement for titles and descriptions, from the Arial advance widths,
  because characters are the wrong unit. Labelled an estimate in every output.
- A robots.txt engine implementing RFC 9309 group precedence, longest match, and
  `*` and `$` patterns, which `urllib.robotparser` does not. Reports blocked
  crawlers separated by whether blocking them costs citations now or only affects
  future training.
- Baselines and drift detection in SQLite, giving the pack a memory: 18 tracked
  fields, 19 comparison rules with fixed severities, and the rule that fired
  named in the output.
- Search Console CSV analysis, so the pack is useful with no paid tool: totals
  with impression-weighted position, striking distance, CTR outliers benchmarked
  against the export itself, cannibalisation, and period on period comparison.
  Tolerant of English and German headers, either delimiter, either decimal
  separator, and a byte order mark.
- 140 tests, run with `python -m unittest discover -s tests -t .`, no test runner
  to install. Includes a local fixture server for the network path.
- `.github/workflows/ci.yml`: Linux, Windows and macOS on Python 3.9 and 3.13,
  a CLI smoke test, a secret scan, a plugin-mirror sync check, and a guard that
  fails the build if a dependency file ever appears.
- `docs/execution-layer.md`, the full command reference, the deliberate limits,
  and how to use the tools from Claude Code and from ChatGPT.
- A `## Tools` section in the 17 skills that have a tool behind them.

### Changed

- `scripts/validate.py` now also checks that every `python -m seo_tools <command>`
  a skill or doc mentions is a command that exists, and warns about commands
  nothing references.
- `AGENTS.md` tells agents to measure with the tools rather than infer from
  markup, and carries the rules for editing the tools.

### Fixed

- `scripts/validate.py` reported a false sibling reference for any URL path in an
  example output block, so `/pricing` looked like a missing skill. Sibling
  references are now checked in prose only.
- `safety.validate_url`: `allow_private`, the test-only escape hatch, was
  propagating through every redirect hop, so a fixture server could redirect a
  test into a cloud metadata endpoint. It now relaxes only the private-address
  range check; schemes, credentials, local hostnames and metadata addresses stay
  blocked either way.
- `gsc`: accents were folded after ASCII punctuation stripping, which deleted
  them, so no German export header ever matched.
- `gsc`: the thousands separator was decided per cell, making "4.000" four in one
  row and four thousand in the next. The locale is now decided once per file.
- `parsing`: text in nested elements inside a heading or link ran together, so a
  Webflow H1 built from stacked spans read as "Procurementmade simple".
- `parsing`: a heading whose closing tag never arrived was dropped entirely,
  producing a false "no H1" critical finding on pages that had one.
- `cli`: `--json` after the command name was a usage error, and the natural
  invocation is the one everybody writes.

## [0.1.0] 2026-08-26

First release. Twenty-five skills across five lanes.

### Added

- **Set up:** `seo-profile-setup`, `site-inventory`.
- **Research:** `keyword-discovery`, `serp-analysis`, `competitor-gap`, `keyword-prioritisation`, `keyword-page-mapping`, `demand-trends`.
- **Optimise:** `content-brief`, `meta-writer`, `heading-architect`, `page-optimiser`, `snippet-targeting`, `schema-builder`, `internal-linking`.
- **Audit:** `technical-audit`, `cannibalisation-audit`, `content-decay`, `indexation-check`, `performance-report`.
- **AI visibility:** `ai-crawler-access`, `ai-visibility-audit`, `citation-gap`, `geo-rewrite`, `prompt-panel`.
- The profile system: `profiles/PROFILE.template.md` plus a worked example, read by every skill at Step 0.
- `PRINCIPLES.md`, the evidence and no-black-hat rules that override any individual skill.
- `docs/data-sources.md`, the Ahrefs and Peec AI tool mappings, unit conventions, and the no-connector fallback for every data need.
- `docs/skill-template.md` and `scripts/validate.py`, so contributed skills keep the same shape.
- Claude plugin marketplace manifest, and `install.sh` for local agents.
