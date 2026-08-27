# The execution layer

Skills reason. Tools measure. This is the measuring half.

Everything on this page runs from a clone with the Python already on your
machine. No `pip install`, no requirements file, no API key, no account. If
that stops being true, the CI job that checks for dependency files will fail,
which is deliberate.

## Why it exists

A skill written only as prose has to ask a model to read a page and report what
the title is. That works most of the time, which is the problem: the failures
are invisible and nothing can be re-checked. A measurement that comes out of
`parse_page` is the same measurement tomorrow, a test can pin it, and when it is
wrong the bug has a line number.

So the division is fixed. Tools produce numbers and facts. Skills decide which
of them matter to this business, in what order, and what to do about them. A
tool never advises, and a skill never invents a number.

## Getting started

```bash
python -m seo_tools doctor
```

Checks the Python version, storage, outbound HTTPS and console encoding, and
prints a fix for anything missing. Then:

```bash
python -m seo_tools page https://example.com/pricing
```

Add `--json` to any command for the machine-readable form, which is what the
skills use. The flag works before or after the command name.

## Commands

| Command | What it answers |
|---------|-----------------|
| `doctor` | Will this run on my machine, and what is missing |
| `fetch <url>` | What the server actually returns: status, redirect chain, SEO headers, encoding |
| `page <url>` | Everything measurable on one page, plus the findings |
| `meta <url>` | Do the title and description fit, in pixels |
| `headings <url>` | What the heading outline really is, and where it breaks |
| `schema <url>` | Does the JSON-LD parse, and does each type carry its required properties |
| `robots <url>` | Which AI and search crawlers may fetch this URL, and which rule decided |
| `sitemap <url>` | Which sitemaps exist, which are declared, which are reachable |
| `baseline <url>` | Store the current state as a known good snapshot |
| `drift <url>` | What changed against that snapshot, and how badly |
| `history <url>` | Which snapshots and comparisons are held for a URL |
| `gsc <csv>` | What a Search Console export says, with no API access |
| `crawl <csv>` | What a crawl export says: any exporter, no API access |

Shared flags: `--json`, `--timeout`, `--user-agent`, `--home`.

Exit codes: `0` it answered, `1` it could not or found something critical,
`2` the arguments were wrong. `page` and `drift` return `1` on a critical
finding, so a release script can gate on them.

### page

The workhorse. Extracts title, description, canonical, robots directives,
`lang`, hreflang, the full heading list, Open Graph and Twitter tags, JSON-LD
blocks and their types, word counts for the whole document and the main content
separately, image and alt counts, internal and external link counts, and
whether the content appears to be client-rendered. Then runs the checks in
`seo_tools/audits.py` and returns findings sorted worst first.

No JavaScript is executed. That is a choice, not a gap: a page whose text only
appears after hydration reports `requires_js: true`, which is the finding, since
most AI crawlers do not execute JavaScript either.

### meta

Measures in pixels, because characters are the wrong unit. "Illinois" and
"Wholesale" are both nine characters and one is nearly twice the width of the
other, so a title inside the character limit can still truncate.

The widths are the published Arial advance widths scaled to the SERP font size.
It is an estimate: no kerning, no font fallback, and Google rewrites titles
anyway. Every output says so in a `method` field, and any skill quoting the
number has to carry that label with it.

Works without a URL, which is the useful part when drafting:

```bash
python -m seo_tools meta --title "Your draft title" --description "Your draft description"
```

### robots

Implements RFC 9309 properly: the most specific user-agent group wins, then the
longest matching path pattern, then a tie goes to allow. `*` and `$` are
supported. `urllib.robotparser` does none of this, which is why this module
exists.

The output separates blocked crawlers by what blocking them costs:

- **live fetch** (ChatGPT-User, Claude-User, Perplexity-User) cannot open your
  page when someone asks about you. Costs citations immediately.
- **search index** (OAI-SearchBot, PerplexityBot, Claude-SearchBot, Googlebot,
  Bingbot) drops you from the index the answers are drawn from.
- **training** (GPTBot, ClaudeBot, CCBot, Google-Extended and others) affects
  future models only. Blocking these costs you nothing today.

Conflating those three is the most common and most expensive mistake in this
area. In particular, blocking `Google-Extended` does not remove you from Google
Search or from AI Overviews, which use Googlebot. There is a test pinning that.

### baseline, drift, history

The pack's memory. `baseline` snapshots 18 fields plus a hash of the HTML and of
the schema. `drift` re-fetches and applies 19 rules, each with a fixed severity,
so the same change always classifies the same way and the rule that fired is
named in the output.

Severity is not the size of the change. A rewritten title is a warning because
someone probably meant it. A canonical that moved overnight is critical because
nobody does that on purpose.

```bash
python -m seo_tools baseline https://example.com/pricing --label "before the rebuild"
# ship something
python -m seo_tools drift https://example.com/pricing
python -m seo_tools history https://example.com/pricing
```

Storage is SQLite, in the first of these that applies: `SEO_SKILLS_HOME`, a
project-local `.seo/` directory if one exists, otherwise the user cache
directory. Project-local is preferred so a baseline travels with the project it
describes, and `.seo/` is already in `.gitignore`.

### gsc

The one that makes this useful with no paid tool at all. Anyone with a verified
property can export a CSV, and that export is real received traffic rather than
a model of it.

```bash
python -m seo_tools gsc queries.csv
python -m seo_tools gsc now.csv --compare before.csv --dimension page
```

Handles what the exports actually look like: English or German headers, comma or
semicolon delimiters, percent CTR, either decimal separator, a byte order mark.
It reports which columns it recognised and which it ignored rather than assuming.

Four analyses:

- **totals**, with average position weighted by impressions, which is not the
  mean of the position column.
- **striking distance**: rows at positions 8 to 20 with impressions to convert.
  Not "easy wins", just where a position gain would turn existing impressions
  into clicks.
- **CTR outliers**: rows well below the median CTR for their own position band.
  The benchmark is your own export, not a published curve whose provenance you
  cannot check.
- **cannibalisation**: queries where more than one URL takes a real share of
  impressions. Needs query and page on the same row, which the Search Console
  UI does not export. Use the API with both dimensions, or Looker Studio. Given
  a queries-only file it says so instead of guessing.

`--compare` joins two exports and ranks what moved. It cannot verify that the
two files cover equal-length, non-overlapping periods, so it states that
assumption in the output rather than hiding it.

### crawl

The other import path, and the one that makes the provider genuinely swappable.
Screaming Frog, Sitebulb, Semrush Site Audit, Ahrefs Site Audit and a hand-built
spreadsheet all describe the same thing, so all of them are mapped onto one
canonical row and every analysis reads that row rather than a vendor's columns.

```bash
python -m seo_tools crawl screamingfrog.csv
python -m seo_tools crawl export.csv --thin 500 --json
python -m seo_tools crawl odd.csv --columns url,status,title,-,canonical
```

Answers with no API and no network: status bands, broken URLs ordered by inlinks
so severity is visible, redirect chains found within the crawl, duplicate titles
and descriptions and H1s, missing fields, canonicals pointing elsewhere, orphans,
and thin pages.

Two judgement calls are built in. Duplicates and missing-field counts ignore
non-indexable pages, because a duplicate title on a noindexed thank-you page
competes with nothing and reporting it buries the pair that does. And the
thin-page threshold is an argument rather than a rule, because a 200-word pricing
page can be exactly right.

## Locales

The pack is for anyone, so no tool here assumes English or a Western market. Four
places where that assumption is easy to make silently, and what each one does
instead:

**Word counts.** Chinese and Japanese do not put spaces between words, so counting
letter runs returns 1 for an entire sentence. Those scripts are counted per
character, which is also how word counts are conventionally reported in them.
Korean uses spaces and is counted by words. `page` reports `word_count_basis` so
the caller knows which applies. Thai, Lao, Khmer and Burmese have neither word
spaces nor a usable character unit; segmenting them needs a dictionary, which
would mean a dependency, so the basis field says the count is indicative only.

**Title and description width.** Wide and fullwidth characters are measured at one
em, roughly double a Latin lowercase letter. Measured as Latin, a CJK title that
truncates reports as fitting. Combining marks are measured at zero, so accented
and Indic text is not charged twice for one glyph. The estimate is rougher for
non-Latin scripts because Google renders them in a different font, and the
`method` field on every measurement says which basis was used.

Every pass or fail decision about length is made in pixels. Character counts are
reported because that is what briefs are written against, but they never decide
anything: a character count is not comparable across scripts.

**Search Console exports.** Google localises the export header. The aliases cover
English, German, French, Spanish, Italian, Dutch, Polish, Turkish, Czech, Swedish,
Japanese, Korean, Chinese and Russian. For anything else, name the columns
positionally and skip what you do not need:

```bash
python -m seo_tools gsc export.csv --columns query,clicks,impressions,-,position
```

The result reports `columns_resolved_by` so it is clear whether the header was
recognised or overridden.

**Crawlers.** `robots` covers the engines that lead outside the US as well as the
AI crawlers: YandexBot, Baiduspider, Yeti (Naver), SeznamBot, PetalBot. A profile
that names one of those markets should read those rows first. Applebot is listed
separately from Applebot-Extended, because one governs search visibility and the
other only training, which is the same trap as Google-Extended.

Cyrillic, Greek and Hebrew are measured from real font metrics, extracted by
`scripts/extract_font_widths.py` rather than transcribed by hand. Those three
scripts render one glyph per codepoint with a fixed advance, which is the
condition under which summing per-character widths means anything. Running that
script with `--verify` also checks the hand-written Latin table against the font;
it found one error, a sharp s recorded as 556 when the font says 611.

Two script families are **not** measurable this way, and the tools say so instead
of producing a number. Arabic is cursive: letters join and change form depending
on their neighbours, so an isolated codepoint's advance is not what renders. The
Indic scripts form conjuncts and reorder vowel signs, and Arial contains no
Devanagari at all, so anything measured there belongs to a substituted font. For
text in either, `method` begins with `UNRELIABLE`, the width is labelled a floor
rather than an estimate, and `page` and `meta` emit `title.width_unmeasurable`
instead of a truncation verdict. A pass or fail on a number that does not mean
what it looks like is worse than no verdict.

To add a script, regenerate the table from a font that contains it:

```bash
python3 scripts/extract_font_widths.py --font /path/to/arial.ttf --write-module
```

Liberation Sans is metrically identical to Arial and openly licensed, so it
produces the same table if you would rather not read a proprietary font.

## Using it from an agent

### Claude Code

Skills call the commands directly through Bash. The `## Tools` section in each
skill lists the exact invocation. Nothing else to configure.

### ChatGPT

Two paths, and the difference matters:

- **Codex, or any local agent that can run shell commands.** Point it at the
  clone. It reads `AGENTS.md`, and the commands work as they do anywhere else.
  This is the path that behaves like Claude Code.
- **ChatGPT in the browser.** Its Python sandbox has no network access, so
  `page`, `robots` and `sitemap` cannot reach a site from inside it. What works:
  run the command on your own machine, then paste the `--json` output into the
  conversation. `gsc` is the exception and works fully, because it reads a file
  you upload rather than the network.

Do not wire these into a Custom GPT Action. That would mean hosting the tools
somewhere and pointing a third party at them, which is a different project with
different security questions.

## Extending it

A new command is a function in `seo_tools/cli.py` plus a `sub.add_parser` entry,
with the logic in a module beside it so tests can reach it without going through
argparse. Rules for anything added here:

1. Standard library only.
2. Return findings as data. An `id`, a severity, what was observed. No prose.
3. Never invent a number. If something is an estimate, say so in the output.
4. Every URL goes through `safety.validate_url`. Never call `urllib` directly.
5. A test per behaviour, and a test for the failure mode.
6. A skill that mentions the command, or `scripts/validate.py` will warn.

## Deliberate limits

- **No JavaScript execution.** Adding it means a browser engine, which breaks
  the no-install promise. `requires_js` flags the case instead.
- **No Core Web Vitals.** Field data needs the CrUX or PageSpeed API and a key.
  Out of scope while the promise is zero setup.
- **No crawler.** These tools work on a page or a supplied list, not a site
  sweep. Feed them from `sitemap --expand`.
- **`gsc` reads exports, it does not call the API.** An OAuth flow is a
  different kind of project.
