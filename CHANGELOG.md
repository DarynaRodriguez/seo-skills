# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] 2026-08-28

A fifth agent, a new skill, and a sourcing rule that removed a decade of folklore
from the pack's own prose. The theme: state where a recommendation comes from, or
do not make it.

### Added

- **`seo-brief-writer`**, the fifth agent. The pack could say what was wrong with a
  page and never what should be written instead. `/content-brief` covered that for
  one page in conversation; there was no agent, so a page set could not be briefed
  in parallel the way it can be audited. It writes two files per page, markdown for
  the writer and JSON for aggregation, and it passed the existing contract tests
  with no changes, which is the first evidence those tests generalise past the
  agents they were written for.
- **A closed recommendation set the writer can refuse with**: `write`, `rewrite`,
  `merge`, `do_not_publish`, `blocked`. `angle_found: false` forces
  `do_not_publish`, and the definition says outright not to soften a refusal
  because a brief was requested. An agent that can only say yes is a content mill
  with a schema.
- **`blocked`, with a `blocking_issue` field coupled to it in both directions.** Six
  live briefs all hit a URL that answered HTTP 200, sat in the sitemap and rendered
  the application's own 404. The enum had no value for it, so three agents each
  invented a different key: `critical_blocker`,
  `critical_finding_not_in_contract`, `recommendation_caveat`. Three names for one
  thing, unreadable to any orchestrator comparing files.
- **`/accessibility-audit`**, and the discovery behind it: the pack already ran four
  WCAG success criteria and never said so. `images.missing_alt` is 1.1.1,
  `heading.level_skipped` is 1.3.1, `lang.missing` is 3.1.1, `mobile.no_viewport`
  is 1.4.10. Every one of those findings now carries its criterion and conformance
  level, so it can serve the accessibility work it was always evidence for.
- **`docs/google-guidance.md`**, the source of record. Citations with the date they
  were fetched, the myths Google names explicitly, and a section stating where this
  pack knowingly goes beyond Google. A pack claiming everything traced to Google
  would be lying, and that section is what makes the rest credible.
- `urls_truncated` and `urls_shown` on grouped crawl findings, so a capped list says
  it is capped.

### Changed

- **Titles and descriptions are measured, not counted.** Google publishes no
  character limit for either and truncates to fit the device width. `meta-writer`
  said 50 to 60 characters and `site-inventory` flagged rows over 60 and over 155,
  while `seo.py meta` measured pixel width the whole time. The folk rules are gone
  from every skill, and a test scans normalised paragraphs to keep them out.
- **"Required" in schema now means required by Google for a rich result.**
  Schema.org requires nothing: no property is ever mandatory, entities may carry
  properties from several types, and text where an object is expected is explicitly
  not an error. Google draws the lines because Google decides eligibility. A
  missing property is an eligibility problem, never a validity error.
- **Performance claims are bounded by Google's own words.** Core Web Vitals are
  used by its ranking systems, and there is no single page experience signal, good
  scores guarantee nothing, and Search shows the most relevant content even where
  page experience is sub-par. Both halves are quoted. `technical-audit` gains
  provider rows for CrUX and Lighthouse and states plainly that `seo.py` cannot
  measure any Core Web Vital, because it never renders.
- The AI skills lead with Google's position that AI features need no special
  optimization and that AEO and GEO are SEO reframed. They earn their place because
  the reporting differs, not the work, and they say so in those words.
- `validate.py` treats any `mcp__` prefixed tool as host-provided. Enumerating one
  host's MCP names would make the pack warn on every other host's.

### Fixed

- **`@id` reference stubs were reported as missing required properties.** A node
  carrying an `@id` and no properties of its own points at a definition elsewhere,
  which is the entire purpose of `@id`. Nodes carrying real properties are still
  checked.
- **Two stale rich-result claims.** `Course` was listed as retired while Google
  documents a Course list feature. `FAQPage` carried 2023 wording about health and
  government sites; it, `HowTo` and `Book` now have no entry in the structured data
  gallery at all. Every remaining entry carries the date it was checked, and a test
  enforces that, because a stale "no rich result" note is the same defect as a stale
  "use this" note.
- **A silent cap.** `duplicates()` trimmed its URL list to 20 while `count` reported
  the real size, so a crawl analyst reading `len(urls)` put a 31-page finding at 20.
- **"No profile" had no documented spelling.** The orchestrator passes the literal
  string `none`; no agent definition said so, and two runs each decided alone what a
  path-shaped value meaning an absence was.
- **`seo-ai-access-checker` documented none of its five inputs**, and was asked a
  question its own toolset cannot answer: `seo.py` never executes JavaScript, so it
  cannot say what a rendering crawler sees. The limit is stated, a browser tool is
  named where one exists, and both numbers have fields.
- `seo-brief-writer`'s frontmatter declared only `Bash, Read, Write` while its body
  told the agent to read the rendered DOM, so a real subagent could never have done
  it.
- A real null byte in this changelog, inside the entry describing the null-byte
  hostname bypass. A heredoc had collapsed the escape into the byte it documented,
  making the file binary to every text tool that opened it.

### Testing

334 tests, up from 232 at 0.5.0's start. `tests/test_agent_contract.py` treats the
agent definitions and the skills as a contract with the tools and with the
documentation: every field an agent is told to copy must exist, no runnable block
may use the module form, every contract template must parse as JSON, no skill may
state a character limit, and every link presented as Google guidance must resolve
to a real documentation root.

The folklore ban was verified against a planted violation rather than assumed to
work.

## [0.5.0] 2026-08-27

Two rounds of running the four subagents against a live site, each time asking
them to report the defects in their own definitions. The theme of everything
below: a definition named a field, the agent went looking, the field was not
there, and the agent invented a value. Invented values differ per instance, which
breaks the one thing the orchestrator does, namely compare files written by
different agents.

### Added

- **`normalise`**, a fourteenth command. Two datasets describing the same page
  rarely spell its URL the same way, so a join on the raw string matches a
  fraction of the rows and produces a ranking that looks weighted and is not.
  This returns the canonical form. It exists as a command because the previous
  advice was `python -c "from seo_tools.safety import normalise_url; ..."`, which
  fails everywhere except the pack root: the exact defect the launcher exists to
  fix, reintroduced in a code snippet. A string that is not a URL comes back with
  `ok: false` rather than a key, so a caller computing a match rate knows the
  input was junk instead of counting it as a key that failed to match.
- **`checked_at` on every `--json` payload**, a full ISO 8601 instant in UTC.
  Three separate agent runs each invented their own answer to "when was this
  true": one shelled out to `date`, one read the machine clock, one would have
  assumed midnight. A record whose timestamp was improvised cannot be ordered
  against the next one, which is most of what a baseline is for. Stamped in the
  JSON envelope so all fourteen commands carry it and none can forget.
- **`allow_is_implicit` on every robots verdict**, with `implicit_allow_count`
  and `allowed_count` as the site-level pair. "Nothing said no" and "a rule said
  yes" both read as allowed, and only the second survives someone adding a broad
  `Disallow`, so a report that does not separate them calls a weak pass a strong
  one. It is a boolean because a run had to derive it by matching on the wording
  of `reason` across 24 crawlers, which is one rewording away from being silently
  wrong about every one of them.
- `page_facts` in the page auditor's contract gains `meta_robots`,
  `meta_robots_directives`, `title_length`, `canonical_is_self`, `word_count`,
  `images_missing_alt` and `has_viewport`.
- `docs/execution-layer.md` gains a note on path form: Git Bash translates
  `/c/Users/...` for a bare command argument but not inside a quoted `python -c`
  string, where a POSIX-style path silently fails to resolve.

### Fixed

- **The page auditor's definition stated a falsehood.** It claimed the redirect
  chain "is the one thing `page` does not return". It is in the output, and on a
  page that never redirected it holds one entry, the request that answered, so an
  agent copying it verbatim writes a one-element chain while the contract says
  `[]`. Two incompatible conventions in one audit directory. The chain's length
  is not a redirect count; `redirect_count` is.
- **`page_facts` omitted the one fact its own judgement section depends on.** The
  whole section is about suppressing an intended `noindex`, and a reader of the
  output file could not see whether the page carried a robots directive. Found on
  an imprint page, exactly the class a profile lists as never-index.
- **`audit_ai_agents` built its per-agent row by naming four verdict keys**, so
  `allow_is_implicit` was returned one function earlier and silently dropped
  before it reached the CLI. It spreads the verdict now. An enumerated subset of
  someone else's return value looks complete and cannot stay complete.
- **`normalise --json` always exited zero.** The JSON caller is the one most
  likely to be a script reading only the status, so having `--json` succeed on a
  URL it had just rejected was precisely backwards.
- **The drift watcher's `home` fallback pointed somewhere that does not exist.**
  The definition said `home` is "normally the `.seo` directory beside the audit
  output", but the orchestrator puts the output *inside* `home`. The requirement
  to pass it explicitly was load-bearing only because the heuristic underneath
  was broken, so the heuristic is gone rather than corrected.
- **Its no-baseline branch contradicted itself**, telling the agent to write
  `verdict: "no baseline"` in one paragraph and to copy the tool's sentence
  verbatim in another. Both could not hold.
- **Two definitions printed `python -m seo_tools` in runnable command blocks**
  while the prose directly above explained why that form cannot work from an
  agent's working directory. A trap set for the instance that copies before it
  reads.
- **No definition mentioned `PYTHONIOENCODING` on Windows.** Without it a German
  page comes back as mojibake and the failure looks like a fault on the site
  rather than a shell setting. Also `python` versus `python3`, which matters on a
  POSIX box with no `python` shim.
- **The drift and crawl contracts named outputs with nowhere to put them.**
  `inputs_missing` and `counts` were required by the inputs table and absent from
  the JSON template, so instances disagreed about whether the keys existed.
- **A real null byte was sitting in this changelog**, inside the entry describing
  the null-byte hostname bypass. A heredoc had collapsed the escape into the byte
  it was describing, which made the file binary to every text tool that read it.
  It is `%00` now.
- **The crawl analyst's contract required outputs it did not name.** The
  definition mandates a join match rate, an export freshness statement, a coverage
  caveat and an ordering basis, and none had a field, so an agent invented five
  keys. A contract whose mandatory outputs can only be delivered through
  improvised keys is not a contract: the orchestrator cannot read what it never
  specified. `join_match_rate`, `export_date`, `export_freshness`, `coverage`,
  `ordering_basis`, `limitations`, `selection_basis` and `excluded` are named now.
- **`limitations` versus `site_findings` was ambiguous**, and the run showed why it
  matters: a partial export with no homepage is a limitation of the audit, not a
  defect of the site, and filing it as a finding forces a severity onto something
  that has none. The contract now says which key the orchestrator prints.
- **The definition implied the crawl output was the complete factual base.** Title
  width is not a crawl check, so an agent computed one from character counts. It
  now says to take width from the exporter's own pixel columns or from
  `seo-page-auditor`, and never to present a character count as a width.
- **Whether the output directory already exists was unstated.** The orchestrator
  creates it; agents create it if missing rather than failing.
- **Three of the four agents documented a command that cannot work.**
  `python -m seo_tools` resolves only from the pack root, and an agent's working
  directory never is. Only `seo-page-auditor` carried the `seo.py` fallback, and
  even that named a `<pack-root>` the agent had no way to derive. `pack_root` is
  now a declared input on every agent, `site-audit` passes it, and an agent
  without it stops rather than guessing.
- **`seo-drift-watcher` could return a confidently wrong answer.** Its definition
  never mentioned `--home`, so without it `drift` reads a different baseline
  store, finds nothing, and reports `no baseline`, which is indistinguishable from
  a correct result. That is the worst failure shape available. `home` is now a
  required input and `site-audit` passes it.
- **`seo-ai-access-checker` would report a `noindex` page as reachable.** Its job
  is whether the fetchers can reach a page; robots.txt is only one of three ways
  the answer is no. It now checks `meta_robots` and `X-Robots-Tag` too, and the
  verdict enum gained `noindex` and `unknown`.
- **The severity set was never stated**, so an agent invented "notice" and had to
  grep the source to find the real three. All four now state that
  `critical`, `warning`, `info` is closed.
- **`<slug>` was defined in one agent and used in three.** The full rule, including
  leading slashes, casing, and a hash suffix for paths over 80 characters, is now
  in every agent that writes a per-URL file.
- **The page auditor's contract forced lossy output.** `observed` was typed as a
  string while the tools return arrays and objects, so an agent flattened the
  evidence, and there was no field for the estimate label a guardrail requires it
  to carry. Findings now pass through verbatim, and `page_facts`,
  `inputs_missing`, `final_url` and `redirect_chain` exist.
- **Contracts asked for fields the tools did not return.** `drift --json` now
  returns `baseline_label`, so nobody has to open the SQLite file, and a stable
  `verdict_code` beside the sentence, so two agents cannot disagree about the
  mapping. An agent had done both by hand.
- **Unfillable fields had no documented absent value.** `clicks_28d` and
  `clicks_at_risk` are `null` when no click source was supplied, never `0`, since
  zero is a claim about traffic. Timestamps are full ISO 8601, after a run
  produced a `checked_at` earlier than its own `baseline_captured_at`.
- **`maxTurns: 10` was too tight** for the access checker, which used nine calls
  on the happy path with no retries. Raised to 16.
- `AGENTS.md` records the Windows cp1252 trap: an agent reading tool output with
  the default encoding sees mojibake on a German page and concludes the pack
  mis-decodes it. It does not.
- Two test files carried a stray `if __name__` block mid-file from an earlier
  append. In `tests/test_locales.py` it had swallowed two classes, so the suite
  lost seven tests without a single failure. Collapsed to one trailing block per
  file.

### Testing

`tests/test_agent_contract.py` treats the agent definitions as a contract with
the tools and pins it: every field name an agent is told to copy must exist, no
runnable command block may use the module form, every agent must name the Windows
encoding requirement, and each contract template must parse as JSON. A definition
and a tool can no longer drift apart in silence, which is what every entry above
has in common.

267 tests, up from 232.

What worked, across both runs: all output files were valid JSON, the persistence
contract aggregated cleanly, and the judgement sections did their job. One agent
collapsed six duplicate-H1 groups into a single localisation defect, which is the
reframe those sections exist to produce.

## [0.4.1] 2026-08-27

### Security

A security audit by probing rather than reading. Five real weaknesses, each now
pinned by a test in `tests/test_security.py`, and `docs/security.md` records both
what is defended and what is not.

- **Shared address space was reachable.** `100.64.0.0/10`, carrier-grade NAT,
  reports `is_private` as False, so the explicit range list let it through. The
  address check now also requires `is_global`, which additionally excludes the
  benchmarking and documentation ranges.
- **A null byte in a hostname bypassed the guard.** `getaddrinfo` truncates at the
  null, so `http://example.com%00.evil.invalid/` resolved as `example.com`,
  passed validation, and named a different host. Any control character in a URL is
  now refused, which also closes the CR and LF request-smuggling shapes.
- **Decompression was unbounded.** The download cap of 8 MB protected nothing on
  its own: 199 KB of gzip expanded to 200 MB in a test, and ratios above 1000 to 1
  are trivial. Both the gzip and deflate paths now stop at 32 MB.
- **A password in a URL reached stdout and the JSON payload.** Error messages
  echoed the URL they refused, which is useful, and harmful in exactly the case
  where the URL carries credentials. Every URL printed now goes through
  `safety.redact`, and a test asserts the secret appears nowhere for any command.
- **`http.client.InvalidURL` escaped as a traceback.** It subclasses
  `HTTPException`, not `ValueError`, so `fetch` did not catch it. Now caught.
- **IP-shaped hostnames were refused by luck, not by rule.** `0177.0.0.1`,
  `2130706433`, `0x7f000001` and `127.1` were blocked on Windows only because the
  resolver happened to fail on them. CI on macOS accepted `0177.0.0.1`, because
  `getaddrinfo` there parses octal and short forms. A host that looks numeric now
  has to parse as a valid address or be refused outright, and the test asserts the
  refusal comes with that reason rather than from a DNS failure, so the guard
  cannot silently depend on the platform again.
- **IPv4-mapped IPv6 addresses were classified by interpreter version.** Python
  3.13 taught `is_private` and `is_loopback` to look through the mapping and 3.9
  does not, so `::ffff:127.0.0.1` was judged differently depending on the runtime.
  Such addresses are now unmapped before the check, so every version agrees.
  Caught by CI on 3.9 only.
- **Line endings were CRLF in the index despite `.gitattributes` declaring LF**,
  which made `sync-plugin.sh` produce a whole-file diff on Linux and failed the
  repo-contract job. Re-normalised with `git add --renormalize`.

Also added, because the pack reads pages nobody controls: a **fetched content**
section in `PRINCIPLES.md` stating that fetched text is data about a page and
never an instruction to follow, repeated in `AGENTS.md` and in each of the four
subagents, since an agent can run without the skill that would otherwise carry it.

Confirmed already sound, and now covered by tests: no shell execution anywhere in
the runtime, all SQL parameterised, XXE refused by the XML parser, `--columns`
validated against a whitelist, nothing written to a path derived from fetched
content, every address a hostname resolves to checked rather than the first, and
every redirect hop revalidated.

Documented rather than implied away: DNS rebinding is not defended against, since
the address is resolved for validation and again for the connection.

### Fixed

An audit of the whole pack from a fresh clone, probing every command with hostile
input rather than reading the code. Three defects, all now pinned by tests.

- **`robots` and `sitemap` printed a traceback on a malformed URL.** Both call
  `fetch` directly instead of through the helper that catches a refused URL, so
  `robots ftp://example.com/` and `sitemap notaurl` crashed at the user. Caught
  centrally in `main()` now, so a command added later cannot reintroduce it.
- **`robots` accepted a URL that every other command refuses.** `robots_url_for`
  reduces a URL to scheme plus host, which silently discards credentials, so
  `http://user:pass@example.com/` succeeded there while `page` rejected it. Both
  `robots` and `sitemap` now validate what the user actually typed before
  deriving anything from it. Found by a test asserting consistency across
  commands, not by inspection.
- **The plugin mirror shipped a README with four broken relative links.** It
  copied the README but not `docs/workflows.md`, `docs/skill-template.md`,
  `CONTRIBUTING.md` or `LICENSE`. The mirror now carries all of `docs/`, plus
  `LICENSE`, `CONTRIBUTING.md` and `AGENTS.md`, and CI fails on a broken relative
  link in either tree.

### Added

- `tests/test_cli_errors.py`: every URL-taking command against ten malformed or
  hostile inputs, asserting a non-zero exit and no traceback, plus a usage error
  for no arguments and a clean failure for a missing file. 209 tests total.

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
