# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

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
