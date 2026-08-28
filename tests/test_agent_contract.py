"""The fields the agent definitions tell agents to copy must actually exist.

Three live agent runs each reported the same class of defect: the definition
named a field, the agent looked for it, it was not there, and the agent invented
a value. The invented values differ per instance, which breaks the one thing the
orchestrator needs, namely comparing files written by different agents.

So the definitions are treated as a contract with the tools, and this pins it.
Every name below is quoted in `agents/*.md` as something to copy verbatim. If a
tool stops emitting one, this fails here rather than in an audit that reads as
clean.
"""
import json
import pathlib
import re
import unittest

from seo_tools import output
from seo_tools.drift import compare
from seo_tools.fetching import SEO_HEADERS, public_summary
from seo_tools.parsing import parse_page
from seo_tools.robots import AI_AGENTS, RobotsTxt

AGENTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "agents"

HTML = """<!doctype html><html lang="de"><head>
<title>Beschaffungssoftware fuer den Mittelstand</title>
<meta name="description" content="Was die Plattform kostet und fuer wen sie gedacht ist.">
<meta name="viewport" content="width=device-width">
<link rel="canonical" href="https://example.com/de/preise">
<link rel="alternate" hreflang="en" href="https://example.com/pricing">
<script type="application/ld+json">{"@type":"Product","name":"Widget"}</script>
</head><body><main><h1>Preise</h1><h2>Pakete</h2>
<p>%s</p>
<img src="/a.png"><img src="/b.png" alt="described">
<a href="/de/kontakt">Kontakt</a><a href="https://elsewhere.example/x">extern</a>
</main></body></html>""" % ("Wort " * 200)


class TestPageFactsAreAllReal(unittest.TestCase):
    """Every name in the page-auditor's `page_facts` list comes from parse_page."""

    PAGE_FACTS = (
        "title",
        "title_length",
        "meta_description",
        "canonical",
        "canonical_is_self",
        "meta_robots",
        "meta_robots_directives",
        "html_lang",
        "hreflang",
        "word_count",
        "main_word_count",
        "word_count_basis",
        "schema_types",
        "links_internal",
        "links_external",
        "images",
        "images_missing_alt",
        "has_viewport",
        "requires_js",
    )

    def setUp(self):
        self.page = parse_page(HTML, "https://example.com/de/preise")

    def test_every_page_fact_exists(self):
        for field in self.PAGE_FACTS:
            with self.subTest(field=field):
                self.assertIn(field, self.page)

    def test_the_definition_and_this_test_list_the_same_fields(self):
        # Otherwise a field added to the definition is never checked, which is
        # the same silence that produced the defect in the first place.
        text = (AGENTS_DIR / "seo-page-auditor.md").read_text(encoding="utf-8")
        block = text.split("`page` output:", 1)[1].split("`meta_robots` and", 1)[0]
        named = set(re.findall(r"`([a-z_]+)`", block))
        self.assertEqual(named, set(self.PAGE_FACTS))

    def test_both_word_counts_are_present_and_can_differ(self):
        # The basis label qualifies a number, so shipping it with only one of the
        # two is how a page of navigation reads as a page of content.
        self.assertIsNotNone(self.page["word_count_basis"])
        self.assertGreaterEqual(self.page["word_count"], self.page["main_word_count"])

    def test_meta_robots_is_present_even_when_the_page_has_none(self):
        # The suppression judgement depends on this, so absent has to mean absent
        # rather than missing.
        self.assertIsNone(self.page["meta_robots"])
        self.assertEqual(self.page["meta_robots_directives"], [])


class TestRedirectChainIsNotACount(unittest.TestCase):
    """The chain holds the answering request too, so its length is not a count.

    A live run had a one-entry chain on a page that never redirected while the
    contract said to write `[]`. Two agents reading that differently is two
    incompatible conventions in one audit directory.
    """

    def summary_for(self, chain, count):
        return public_summary({
            "ok": True,
            "url": "https://example.com/a",
            "final_url": "https://example.com/a",
            "status": 200,
            "headers": {"content-type": "text/html"},
            "redirect_chain": chain,
            "redirect_count": count,
            "bytes": 0,
            "truncated": False,
            "encoding": "utf-8",
            "encoding_source": "header",
            "elapsed_ms": 12.0,
        })

    def test_a_direct_hit_reports_zero_redirects_with_a_non_empty_chain(self):
        summary = self.summary_for([{"url": "https://example.com/a", "status": 200, "location": None}], 0)
        self.assertEqual(summary["redirect_count"], 0)
        self.assertEqual(len(summary["redirect_chain"]), 1)

    def test_redirect_count_is_the_field_to_read(self):
        chain = [
            {"url": "https://example.com/a", "status": 301, "location": "/b"},
            {"url": "https://example.com/b", "status": 200, "location": None},
        ]
        summary = self.summary_for(chain, 1)
        self.assertEqual(summary["redirect_count"], 1)
        self.assertEqual(len(summary["redirect_chain"]), 2)

    def test_the_definition_tells_the_agent_to_read_the_count(self):
        text = (AGENTS_DIR / "seo-page-auditor.md").read_text(encoding="utf-8")
        self.assertIn("redirect_count", text)
        self.assertNotIn("the one thing `page` does not return", text)

    def test_x_robots_tag_survives_the_header_whitelist(self):
        # The access-checker reports a missing header as "no header sent", which
        # is only true while this header is kept.
        self.assertIn("x-robots-tag", SEO_HEADERS)


class TestDriftReturnsWhatTheWatcherCopies(unittest.TestCase):
    FIELDS = ("baseline_label", "verdict", "verdict_code", "counts", "total_changes")

    def test_every_field_the_watcher_copies_is_returned(self):
        baseline = {
            "baseline_id": 1,
            "captured_at": "2026-07-02T09:11:40+00:00",
            "label": "before the migration",
            "snapshot": parse_page(HTML, "https://example.com/de/preise"),
        }
        result = compare(baseline, parse_page(HTML, "https://example.com/de/preise"))
        for field in self.FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, result)

    def test_the_no_baseline_branch_is_described_once_and_consistently(self):
        # The definition used to say to write `verdict: "no baseline"` in one
        # place and to copy the tool's sentence in another. Both cannot hold.
        text = (AGENTS_DIR / "seo-drift-watcher.md").read_text(encoding="utf-8")
        self.assertIn('`verdict_code: "no_baseline"`', text)
        self.assertNotIn('`verdict: "no baseline"`', text)


class TestAccessCheckerFieldsExist(unittest.TestCase):
    def test_allow_is_implicit_is_returned_for_every_ai_agent(self):
        robots = RobotsTxt("User-agent: *\nDisallow: /private/\n", 200)
        for agent in AI_AGENTS:
            with self.subTest(agent=agent):
                self.assertIn("allow_is_implicit", robots.can_fetch(agent, "https://example.com/p"))

    def test_the_definition_no_longer_asks_the_agent_to_infer_it(self):
        text = (AGENTS_DIR / "seo-ai-access-checker.md").read_text(encoding="utf-8")
        self.assertIn("the tool's `allow_is_implicit`, copied", text)


class TestNoAgentIsToldToUseTheModuleForm(unittest.TestCase):
    """An agent's working directory is never the pack root, so `-m` cannot work.

    Every agent worked this out from prose, but two definitions still printed the
    failing form in their runnable command blocks, which is a trap set for the
    one instance that copies before it reads.
    """

    def test_no_runnable_command_block_uses_the_module_form(self):
        for path in sorted(AGENTS_DIR.glob("*.md")):
            with self.subTest(agent=path.name):
                for block in re.findall(r"```bash\n(.*?)```", path.read_text(encoding="utf-8"), re.S):
                    self.assertNotIn("python -m seo_tools", block)

    def test_every_agent_names_the_windows_encoding_requirement(self):
        # Without it a non-English page reads as mojibake, and the failure looks
        # like a fault on the site rather than in the shell.
        for path in sorted(AGENTS_DIR.glob("*.md")):
            with self.subTest(agent=path.name):
                self.assertIn("PYTHONIOENCODING=utf-8", path.read_text(encoding="utf-8"))


class TestEveryContractTemplateParses(unittest.TestCase):
    """The JSON blocks in the definitions are what agents copy. They must be JSON.

    Placeholder syntax is allowed inside string values only. A template with a
    bare `<ISO date>` where a value belongs is one an agent has to repair, and
    each instance repairs it differently.
    """

    PLACEHOLDER = re.compile(r'"[^"]*\|[^"]*"')

    def test_json_blocks_parse_after_placeholders_are_removed(self):
        checked = 0
        for path in sorted(AGENTS_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for block in re.findall(r"```json\n(.*?)```", text, re.S):
                cleaned = self.PLACEHOLDER.sub('"placeholder"', block)
                cleaned = re.sub(r'"<[^"]*>"', '"placeholder"', cleaned)
                with self.subTest(agent=path.name):
                    json.loads(cleaned)
                checked += 1
        self.assertGreater(checked, 3, "expected a contract template per agent")


class TestStampIsInEveryEnvelope(unittest.TestCase):
    def test_the_helper_and_the_envelope_agree(self):
        self.assertTrue(output.checked_at().endswith("+00:00"))

    def test_all_four_definitions_tell_the_agent_to_copy_the_stamp(self):
        for path in sorted(AGENTS_DIR.glob("*.md")):
            with self.subTest(agent=path.name):
                self.assertIn("the tool's `checked_at`, copied", path.read_text(encoding="utf-8"))


class TestTheAuditRowKeepsWhatTheVerdictSays(unittest.TestCase):
    """The per-agent row must not be an enumerated subset of the verdict.

    It was, and so `allow_is_implicit` was returned by can_fetch and silently
    dropped one function later. A row built by naming four keys looks complete
    and cannot stay complete, so it spreads the verdict now.
    """

    def audit(self, body, status=200):
        return RobotsTxt(body, status).audit_ai_agents("https://example.com/page")

    def test_every_row_carries_every_verdict_key(self):
        result = self.audit("User-agent: *\nDisallow: /private/\n")
        verdict_keys = set(
            RobotsTxt("User-agent: *\nDisallow: /private/\n").can_fetch(
                "GPTBot", "https://example.com/page"
            )
        )
        for row in result["agents"]:
            with self.subTest(agent=row["agent"]):
                self.assertTrue(verdict_keys.issubset(set(row)))

    def test_a_wholly_permissive_site_reports_every_pass_as_implicit(self):
        result = self.audit("")
        self.assertEqual(result["implicit_allow_count"], result["allowed_count"])
        self.assertEqual(result["blocked_count"], 0)

    def test_an_explicit_allow_is_not_counted_as_implicit(self):
        body = "\n".join(
            ["User-agent: {}\nAllow: /\n".format(agent) for agent in AI_AGENTS]
        )
        result = self.audit(body)
        self.assertEqual(result["implicit_allow_count"], 0)
        self.assertEqual(result["allowed_count"], len(AI_AGENTS))

    def test_the_two_counts_never_exceed_the_crawler_list(self):
        for body in ("", "User-agent: *\nDisallow: /\n", "User-agent: GPTBot\nDisallow: /page\n"):
            with self.subTest(body=body):
                result = self.audit(body)
                self.assertEqual(
                    result["allowed_count"] + result["blocked_count"], len(result["agents"])
                )
                self.assertLessEqual(result["implicit_allow_count"], result["allowed_count"])

    def test_the_definition_names_the_aggregate(self):
        text = (AGENTS_DIR / "seo-ai-access-checker.md").read_text(encoding="utf-8")
        self.assertIn("implicit_allow_count", text)


class TestTheNoProfileConventionIsStated(unittest.TestCase):
    """Every agent that can receive a profile must say how "no profile" is spelled.

    The orchestrator passes the literal string `none`, which reads like a path and
    means an absence. Two live runs each decided that alone and wrote a note
    explaining the reasoning, which is a spec gap wearing the clothes of a
    judgement call.
    """

    TAKES_A_PROFILE = (
        "seo-page-auditor.md",
        "seo-ai-access-checker.md",
        "seo-crawl-analyst.md",
    )

    def test_each_one_spells_it_out(self):
        for name in self.TAKES_A_PROFILE:
            with self.subTest(agent=name):
                text = (AGENTS_DIR / name).read_text(encoding="utf-8")
                self.assertIn('"No profile" is spelled `none`', text)

    def test_the_orchestrator_passes_what_the_agents_expect(self):
        skill = AGENTS_DIR.parent / "skills" / "site-audit" / "SKILL.md"
        self.assertIn("the word `none`", skill.read_text(encoding="utf-8"))


class TestTheRenderGapIsDeclared(unittest.TestCase):
    """The access checker is asked what a rendering crawler sees; its tools cannot say.

    `seo.py` is standard library only and never executes JavaScript. A live run
    answered the question anyway, using a browser tool it happened to have, and
    pointed out that an instance holding only the declared tools would have had to
    call it permanently unknown. The definition now says which it is.
    """

    def setUp(self):
        self.text = (AGENTS_DIR / "seo-ai-access-checker.md").read_text(encoding="utf-8")

    def test_the_limit_is_stated_rather_than_left_to_be_discovered(self):
        self.assertIn("never executes JavaScript", self.text)

    def test_both_word_counts_have_a_field(self):
        for field in ("main_word_count", "main_word_count_rendered", "rendered_check"):
            with self.subTest(field=field):
                self.assertIn(field, self.text)

    def test_the_unrendered_case_has_a_documented_value(self):
        # Otherwise an agent with no browser invents one, and null-because-unchecked
        # becomes indistinguishable from zero-words-rendered.
        self.assertIn("`null` unless you actually loaded the page", self.text)


class TestEveryAgentDeclaresItsInputs(unittest.TestCase):
    """An agent given inputs its definition never names has to guess at them.

    The access checker received url, market, profile_path, output_dir and
    pack_root, and documented none of them, while the other three carried a table.
    """

    def test_each_agent_names_pack_root_and_output_dir(self):
        for path in sorted(AGENTS_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(agent=path.name):
                self.assertIn("pack_root", text)
                self.assertIn("output_dir", text)

    def test_each_agent_has_an_inputs_section(self):
        for path in sorted(AGENTS_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(agent=path.name):
                self.assertTrue(
                    "## Inputs you are given" in text or "## What you are given" in text,
                    "{} documents no inputs".format(path.name),
                )


class TestTheBriefWriterCanSayNo(unittest.TestCase):
    """A brief writer that can only say yes is a content mill with a schema.

    The valuable answer is often "do not publish this", and an agent asked for a
    brief will produce one unless the definition makes refusing a first-class
    outcome with a name.
    """

    def setUp(self):
        self.text = (AGENTS_DIR / "seo-brief-writer.md").read_text(encoding="utf-8")

    def test_the_recommendation_set_is_closed_and_named(self):
        for value in ("write", "rewrite", "merge", "do_not_publish"):
            with self.subTest(value=value):
                self.assertIn("`{}`".format(value), self.text)

    def test_refusing_is_explicitly_permitted(self):
        self.assertIn("Do not soften `do_not_publish`", self.text)

    def test_no_angle_forces_the_refusal(self):
        # Otherwise an agent records angle_found false and recommends writing
        # anyway, which is the failure this coupling exists to prevent.
        self.assertIn('`angle_found: false` forces `recommendation: "do_not_publish"`', self.text)


class TestTheBriefWriterCannotInventNumbers(unittest.TestCase):
    """Every figure carries a source or is null. A brief's whole value is that.

    Two specific lies are called out because both are easy and both are common:
    a zero standing in for "no data", and a head term's volume standing in for
    the page's opportunity.
    """

    def setUp(self):
        self.text = (AGENTS_DIR / "seo-brief-writer.md").read_text(encoding="utf-8")

    def test_absent_volume_is_null_not_zero(self):
        self.assertIn("never `0`", self.text)

    def test_the_head_term_substitution_is_named_as_a_guardrail(self):
        self.assertIn("Never quote the head term's volume as this page's opportunity", self.text)

    def test_questions_must_be_sourced(self):
        self.assertIn("Never invent a reader question", self.text)

    def test_the_render_gap_is_handled_rather_than_ignored(self):
        # Briefing the shell of a client-rendered page describes a page that does
        # not exist, and somebody would act on it.
        self.assertIn("Do not brief the shell", self.text)


class TestTheBriefWriterIsWiredIn(unittest.TestCase):
    def test_a_skill_invokes_it(self):
        # The validator warns on an agent nothing invokes. An agent no skill
        # names is an agent nobody will ever run.
        skills = (AGENTS_DIR.parent / "skills").rglob("SKILL.md")
        named = [p for p in skills if "seo-brief-writer" in p.read_text(encoding="utf-8")]
        self.assertTrue(named, "no skill mentions seo-brief-writer")

    def test_it_writes_both_a_human_file_and_a_machine_file(self):
        text = (AGENTS_DIR / "seo-brief-writer.md").read_text(encoding="utf-8")
        self.assertIn("briefs/<slug>.md", text)
        self.assertIn("briefs/<slug>.json", text)


class TestBlockedIsAFirstClassOutcome(unittest.TestCase):
    """A brief can be correct and still be worthless if the page cannot receive it.

    Six live briefs all hit a URL that answered 200, sat in the sitemap, and
    rendered the app's own 404. Three of the agents each invented a different key
    for that fact, `critical_blocker`, `critical_finding_not_in_contract` and
    `recommendation_caveat`, which is three names for one thing and unreadable to
    any orchestrator comparing files.
    """

    def setUp(self):
        self.text = (AGENTS_DIR / "seo-brief-writer.md").read_text(encoding="utf-8")

    def test_blocked_is_in_the_closed_set(self):
        self.assertIn("| `blocked` |", self.text)

    def test_it_has_a_field_and_not_just_a_verdict(self):
        self.assertIn("blocking_issue", self.text)

    def test_the_field_is_coupled_to_the_verdict_in_both_directions(self):
        self.assertIn(
            "`blocking_issue` is `null` unless `recommendation` is `blocked`, and non-null",
            self.text,
        )

    def test_a_soft_404_is_named_as_its_own_case(self):
        # Distinct from an empty shell: one needs rendering, the other needs a
        # route. Conflating them sends the wrong team.
        self.assertIn("soft\n  404", self.text.replace("\r\n", "\n"))

    def test_the_research_is_not_thrown_away(self):
        self.assertIn("still write the rest of the brief", self.text)


class TestHostProvidedToolsAreNotThisRepoBusiness(unittest.TestCase):
    """The validator must not warn on one host's MCP names.

    Enumerating Claude Code's browser tools in a known-tools list would make the
    pack warn on every other host's, which inverts the purpose of the check. The
    rule is the prefix, not an allowlist.
    """

    def test_an_mcp_tool_does_not_warn(self):
        import subprocess
        import sys

        root = AGENTS_DIR.parent
        result = subprocess.run(
            [sys.executable, str(root / "scripts" / "validate.py")],
            capture_output=True,
            text=True,
            cwd=str(root),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("is not one this repo knows about", result.stdout)

    def test_a_typo_in_a_core_tool_would_still_warn(self):
        # The check still has to catch `Bahs`, or it is doing nothing at all.
        source = (AGENTS_DIR.parent / "scripts" / "validate.py").read_text(encoding="utf-8")
        self.assertIn("KNOWN_TOOLS", source)
        self.assertIn('base.startswith("mcp__")', source)


SKILLS_DIR = AGENTS_DIR.parent / "skills"
DOCS_DIR = AGENTS_DIR.parent / "docs"

# A blank line, however the file was checked out. Built from chr() because this
# pattern has been mangled by a shell heredoc more than once in this repo's history.
BLANK_LINE = re.compile(chr(92) + "n" + chr(92) + "s*" + chr(92) + "n")


def _prose_files():
    """Every file that gives advice to a person or an agent."""
    return sorted(SKILLS_DIR.rglob("*.md")) + sorted(AGENTS_DIR.glob("*.md"))


class TestNoCharacterLimitFolklore(unittest.TestCase):
    """Google publishes no character limit for titles or meta descriptions.

    It says both are truncated to fit the device width, and describes neither as a
    ranking factor. The 60 and 155 character rules are folklore that outlived
    whatever produced them, and they are wrong the moment the text is not English:
    60 characters of Cyrillic is far wider than 60 of Latin, which this pack's own
    width tables demonstrate.

    The pack measures pixels. This stops the character rules coming back.
    """

    BANNED = (
        re.compile(r"\b(?:50|55|60|65|70)\s*(?:to\s*\d+\s*)?characters?\b", re.I),
        re.compile(r"\b(?:140|150|155|160)\s*(?:to\s*\d+\s*)?characters?\b", re.I),
        re.compile(r"over\s+(?:60|155)\s+characters", re.I),
    )

    # Naming the myth in order to reject it is allowed. Stating it as a rule is not.
    REJECTING = ("not Google's", "never were", "far wider than", "flags the wrong rows",
                 "no character limit", "publishes no character limit")

    def test_no_skill_or_agent_states_a_character_limit(self):
        for path in _prose_files():
            # Scan per paragraph, not per line: these files are hard-wrapped, so a
            # rule and its rebuttal routinely land on different lines.
            raw = path.read_text(encoding="utf-8")
            for para in re.split(BLANK_LINE, raw):
                flat = " ".join(para.split())
                if any(marker in flat for marker in self.REJECTING):
                    continue
                for pattern in self.BANNED:
                    with self.subTest(file=path.name, para=flat[:60]):
                        self.assertIsNone(
                            pattern.search(flat),
                            "{} states a character limit: {!r}".format(path.name, flat[:160]),
                        )

    def test_the_width_tooling_is_what_skills_point_at(self):
        meta = (SKILLS_DIR / "meta-writer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("seo_tools meta", meta)
        self.assertIn("no character limit", meta)


class TestGoogleGuidanceExists(unittest.TestCase):
    """One file holds the citations, so a claim can be checked rather than argued."""

    def setUp(self):
        self.path = DOCS_DIR / "source-of-record.md"
        self.text = self.path.read_text(encoding="utf-8")

    def test_it_exists_and_names_its_sources(self):
        self.assertTrue(self.path.exists())
        for page in (
            "ai-optimization-guide",
            "appearance/title-link",
            "appearance/snippet",
            "essentials/spam-policies",
            "javascript-seo-basics",
        ):
            with self.subTest(page=page):
                self.assertIn(page, self.text)

    def test_it_records_the_myths_google_names(self):
        flat = " ".join(self.text.split())
        for myth in ("llms.txt", "no ideal page length", "not required for generative AI search"):
            with self.subTest(myth=myth):
                self.assertIn(myth, flat)

    def test_it_says_where_the_pack_goes_beyond_google(self):
        # A pack that claimed everything traced to Google would be lying: crawler
        # tables, pixel widths and severities are all this pack's own.
        self.assertIn("Where this pack goes beyond Google", self.text)

    def test_the_contributor_rule_is_recorded_where_contributors_read(self):
        agents_md = (AGENTS_DIR.parent / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Google Search Central is the source of record", agents_md)


class TestCitationsPointAtGoogle(unittest.TestCase):
    """A citation that does not resolve is worse than no citation.

    Shape only: this runs offline, so it checks that anything presented as a Google
    source is a developers.google.com/search URL rather than an invented one.
    """

    CITE = re.compile(r"\]\((https?://[^)]+)\)")

    # The documentation roots this pack is allowed to cite as Google's own word.
    # Search Central for search behaviour, /speed for PageSpeed and Core Web Vitals
    # measurement, Search Console Help for what its numbers mean. Anything else on
    # google.com is a blog post, a marketing page or an invention, and none of those
    # is a source of record.
    GOOGLE_DOC_ROOTS = (
        "https://developers.google.com/search/",
        "https://developers.google.com/speed/",
        "https://support.google.com/webmasters/",
    )

    def test_every_google_looking_link_is_a_documented_source(self):
        for path in _prose_files() + [DOCS_DIR / "source-of-record.md"]:
            for url in self.CITE.findall(path.read_text(encoding="utf-8")):
                if "google.com" not in url:
                    continue
                with self.subTest(file=path.name, url=url):
                    self.assertTrue(
                        url.startswith(self.GOOGLE_DOC_ROOTS),
                        "{} cites {} as Google guidance, which is not a documentation root".format(
                            path.name, url
                        ),
                    )


class TestTheAiSkillsAreGrounded(unittest.TestCase):
    """Google says AI features need no special optimization. The AI skills must say so.

    Otherwise the pack sells the thing Google explicitly says is unnecessary, which
    is the whole AEO market's failure mode.
    """

    GROUNDED = (
        "ai-visibility-audit",
        "geo-rewrite",
        "citation-gap",
        "schema-builder",
    )

    def test_each_one_states_googles_position_up_front(self):
        for name in self.GROUNDED:
            text = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=name):
                self.assertIn("What Google says about this", text)
                self.assertIn("developers.google.com/search/", text)

    def test_schema_builder_does_not_claim_ai_requires_markup(self):
        text = (SKILLS_DIR / "schema-builder" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("not required for generative AI search", text)

    def test_the_google_extended_fact_is_stated_not_implied(self):
        text = (SKILLS_DIR / "ai-visibility-audit" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("does not remove a site from AI Overviews", text)


class TestSchemaOrgFlexibilityIsRespected(unittest.TestCase):
    """schema.org requires nothing and permits a great deal. Do not flag valid markup.

    Its data model is explicit: no property is ever required, an entity may hold
    properties from several types, extra properties are allowed, and text where an
    object is expected is not an error. A checker that reports those as defects
    sends people to fix markup that was already correct.
    """

    def findings(self, payload):
        from seo_tools.audits import check_schema

        page = {"schema_blocks": [{"index": 0, "valid_json": True, "data": payload}]}
        return {f["check"] for f in check_schema(page)}

    def test_an_id_reference_is_not_a_missing_definition(self):
        # The whole point of @id: the properties live where it resolves.
        found = self.findings({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "H",
            "publisher": {"@type": "Organization", "@id": "https://e.com/#org"},
        })
        self.assertNotIn("schema.missing_required", found)

    def test_a_graph_with_cross_references_is_clean(self):
        found = self.findings({
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "Organization", "@id": "https://e.com/#org", "name": "Acme"},
                {"@type": "Article", "headline": "H", "publisher": {"@id": "https://e.com/#org"}},
            ],
        })
        self.assertNotIn("schema.missing_required", found)

    def test_multiple_types_on_one_entity_are_allowed(self):
        found = self.findings({
            "@context": "https://schema.org",
            "@type": ["Product", "SoftwareApplication"],
            "name": "N",
        })
        self.assertNotIn("schema.missing_required", found)

    def test_text_where_an_object_is_expected_is_not_flagged(self):
        # schema.org says search engines accept this and do the best they can.
        found = self.findings({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "H",
            "author": "Jane Doe",
        })
        self.assertNotIn("schema.missing_required", found)

    def test_a_partial_node_is_still_checked(self):
        # A node carrying real properties is a definition, not a reference, so the
        # exemption must not swallow it.
        found = self.findings({
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": "https://e.com/#org",
            "url": "https://e.com",
        })
        self.assertIn("schema.missing_required", found)

    def test_a_genuinely_incomplete_type_is_still_flagged(self):
        self.assertIn("schema.missing_required", self.findings({
            "@context": "https://schema.org", "@type": "Article", "name": "N"}))


class TestRequirednessIsAttributedToGoogle(unittest.TestCase):
    """Only Google draws the line, so only Google may be cited for it."""

    def test_the_finding_says_who_requires_it(self):
        from seo_tools.audits import check_schema

        page = {"schema_blocks": [{"index": 0, "valid_json": True,
                                   "data": {"@context": "https://schema.org", "@type": "Article"}}]}
        message = [f for f in check_schema(page) if f["check"] == "schema.missing_required"][0]["message"]
        self.assertIn("Google requires it", message)
        self.assertIn("schema.org itself requires nothing", message)

    def test_the_skill_table_names_google_not_schema_org(self):
        text = (SKILLS_DIR / "schema-builder" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Required by Google", text)
        self.assertIn("required by Google for that rich result, not by", " ".join(text.split()))


class TestRetiredRichResultsAreDated(unittest.TestCase):
    """A stale "no rich result" note is the same defect as a stale "use this" note."""

    def test_every_retired_entry_carries_the_date_it_was_checked(self):
        from seo_tools.audits import SCHEMA_RETIRED

        self.assertTrue(SCHEMA_RETIRED)
        for type_name, note in SCHEMA_RETIRED.items():
            with self.subTest(type=type_name):
                self.assertIn("2026-", note, "{} has no checked-on date".format(type_name))

    def test_course_is_not_listed_as_retired(self):
        # Google documents a Course list feature, so calling Course retired was wrong.
        from seo_tools.audits import SCHEMA_RETIRED

        self.assertNotIn("Course", SCHEMA_RETIRED)

    def test_the_recipes_warn_at_the_point_of_use(self):
        # Somebody copying a block will not have read the skill's preamble.
        recipes = (SKILLS_DIR / "schema-builder" / "references" / "schema-recipes.md").read_text(encoding="utf-8")
        self.assertEqual(recipes.count("**No rich result.**"), 2)

    def test_the_retired_note_does_not_call_the_markup_invalid(self):
        from seo_tools.audits import SCHEMA_RETIRED

        for type_name, note in SCHEMA_RETIRED.items():
            with self.subTest(type=type_name):
                self.assertNotIn("invalid", note.lower())


class TestGoogleStructuredDataPoliciesAreCited(unittest.TestCase):
    def test_the_visible_content_rule_cites_the_policy(self):
        text = (SKILLS_DIR / "schema-builder" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("sd-policies", text)
        self.assertIn("manual action", " ".join(text.split()).lower())

    def test_json_ld_is_named_as_the_recommended_format(self):
        text = " ".join((SKILLS_DIR / "schema-builder" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("Google names it the recommended format", text)

    def test_the_guidance_doc_separates_the_two_sources(self):
        text = (DOCS_DIR / "source-of-record.md").read_text(encoding="utf-8")
        self.assertIn("schema.org/docs/datamodel.html", text)
        self.assertIn("sd-policies", text)
        self.assertIn("only one of them draws lines", text)


class TestAccessibilityFindingsCiteTheirCriterion(unittest.TestCase):
    """Four checks here are WCAG criteria. A reader must be able to look them up.

    They were being reported as SEO findings with no standard attached, which made
    them unusable for the accessibility work they are actually evidence for.
    """

    EXPECTED = {
        "images.missing_alt": "1.1.1",
        "heading.level_skipped": "1.3.1",
        "lang.missing": "3.1.1",
        "mobile.no_viewport": "1.4.10",
    }

    def setUp(self):
        from seo_tools.audits import audit_page

        broken = (
            "<html><head><title>T</title></head><body>"
            "<h1>A</h1><h3>skipped a level</h3>"
            "<img src=a.png><img src=b.png>"
            "</body></html>"
        )
        self.findings = {f["check"]: f for f in audit_page(parse_page(broken, "https://e.com/"))["findings"]}

    def test_each_one_is_raised_and_carries_its_criterion(self):
        for check, criterion in self.EXPECTED.items():
            with self.subTest(check=check):
                self.assertIn(check, self.findings, "{} did not fire".format(check))
                self.assertIn("wcag", self.findings[check])
                self.assertIn(criterion, str(self.findings[check]["wcag"]))

    def test_each_one_names_its_conformance_level(self):
        for check in self.EXPECTED:
            with self.subTest(check=check):
                self.assertRegex(str(self.findings[check]["wcag"]), r"Level A{1,3}\)")

    def test_a_clean_page_raises_none_of_them(self):
        from seo_tools.audits import audit_page

        good = (
            '<html lang="en"><head><title>T</title>'
            '<meta name="viewport" content="width=device-width"></head>'
            "<body><h1>A</h1><h2>B</h2><img src=a.png alt=described></body></html>"
        )
        raised = {f["check"] for f in audit_page(parse_page(good, "https://e.com/"))["findings"]}
        for check in self.EXPECTED:
            with self.subTest(check=check):
                self.assertNotIn(check, raised)

    def test_wcag_appears_only_on_accessibility_findings(self):
        # Otherwise the field stops being a way to filter for them.
        from seo_tools.audits import audit_page

        broken = "<html><head></head><body><h1>A</h1><h3>s</h3><img src=a.png></body></html>"
        for f in audit_page(parse_page(broken, "https://e.com/"))["findings"]:
            if "wcag" in f:
                with self.subTest(check=f["check"]):
                    self.assertIn(f["check"], self.EXPECTED)


class TestTheAccessibilitySkillRefusesToOverclaim(unittest.TestCase):
    """Automated checks find a minority of barriers. A clean run is not a verdict."""

    def setUp(self):
        self.text = (SKILLS_DIR / "accessibility-audit" / "SKILL.md").read_text(encoding="utf-8")
        self.flat = " ".join(self.text.split())

    def test_it_refuses_to_call_a_page_accessible(self):
        self.assertIn("Never call a page accessible", self.text)

    def test_it_names_what_it_cannot_check(self):
        for category in ("Contrast", "keyboard", "ARIA", "tap target"):
            with self.subTest(category=category):
                self.assertIn(category, self.text)

    def test_it_does_not_claim_a_ranking_benefit(self):
        self.assertIn("Never claim accessibility improves ranking", self.text)

    def test_it_protects_deliberate_empty_alt(self):
        # Flagging alt="" teaches people to add noise for screen reader users.
        self.assertIn('Never report `alt=""` as a missing alt', self.flat.replace("  ", " "))

    def test_it_lists_the_four_criteria_the_pack_can_decide(self):
        for criterion in ("1.1.1", "1.3.1", "3.1.1", "1.4.10"):
            with self.subTest(criterion=criterion):
                self.assertIn(criterion, self.text)


class TestPerformanceGuidanceMatchesTheSource(unittest.TestCase):
    """The thresholds are published. Drifting from them is a silent wrong answer."""

    def setUp(self):
        self.flat = " ".join(
            (SKILLS_DIR / "technical-audit" / "SKILL.md").read_text(encoding="utf-8").split()
        )

    def test_the_three_thresholds_are_the_published_ones(self):
        for threshold in ("2.5s or less", "200ms or less", "0.1 or less"):
            with self.subTest(threshold=threshold):
                self.assertIn(threshold, self.flat)

    def test_field_data_is_read_at_the_75th_percentile(self):
        self.assertIn("75th", self.flat)

    def test_the_pack_admits_it_cannot_measure_them(self):
        self.assertIn("This pack cannot measure any of them", self.flat)

    def test_the_ranking_claim_is_bounded_by_googles_own_words(self):
        # Core Web Vitals are used by ranking systems AND good scores guarantee
        # nothing. Stating the first without the second oversells the work.
        self.assertIn("used by its ranking systems", self.flat)
        self.assertIn("do not guarantee a top ranking", self.flat)

    def test_it_cites_both_sources(self):
        self.assertIn("developers.google.com/speed/docs/insights", self.flat)
        self.assertIn("developers.google.com/search/docs/appearance/page-experience", self.flat)

    def test_a_provider_row_exists_for_field_data(self):
        self.assertIn("CrUX", self.flat)


class TestEeatIsStatedAccurately(unittest.TestCase):
    """Two facts about E-E-A-T are routinely inverted, and both change the advice.

    It is not a ranking factor, and trust is the component that matters. A pack
    telling someone to "improve E-E-A-T to rank" is selling a lever that does not
    exist.
    """

    def setUp(self):
        self.quality = " ".join(
            (SKILLS_DIR / "page-optimiser" / "references" / "content-quality.md")
            .read_text(encoding="utf-8").split()
        )
        self.guidance = " ".join((DOCS_DIR / "source-of-record.md").read_text(encoding="utf-8").split())

    def test_it_is_not_sold_as_a_ranking_factor(self):
        for text in (self.quality, self.guidance):
            with self.subTest():
                self.assertIn("not a ranking factor", text)

    def test_trust_is_named_as_the_one_that_matters(self):
        for text in (self.quality, self.guidance):
            with self.subTest():
                self.assertIn("trust is most important", text.lower())

    def test_the_four_letters_are_expanded(self):
        for word in ("Experience", "Expertise", "Authoritativeness", "Trustworthiness"):
            with self.subTest(word=word):
                self.assertIn(word, self.quality)

    def test_the_who_how_why_frame_is_present(self):
        self.assertIn("who, how and why", self.guidance)

    def test_the_authority_collision_is_called_out(self):
        # "Authority" already means link equity in two other skills. Blurring the
        # two produces advice to build links when the problem is an anonymous byline.
        self.assertIn("link equity", self.guidance)
        self.assertIn("different sense of", self.quality)


class TestSearchConsoleSemanticsAreDocumented(unittest.TestCase):
    """Every one of these produces a plausible wrong answer rather than an error."""

    def setUp(self):
        self.guidance = " ".join((DOCS_DIR / "source-of-record.md").read_text(encoding="utf-8").split())
        self.code = (AGENTS_DIR.parent / "seo_tools" / "gsc.py").read_text(encoding="utf-8")

    def test_position_is_documented_as_non_additive(self):
        self.assertIn("not additive", self.guidance)

    def test_position_is_documented_as_not_a_rank(self):
        self.assertIn("Position is not a rank", self.guidance)

    def test_rows_not_summing_to_totals_is_documented(self):
        self.assertIn("do not sum to totals", self.guidance)

    def test_anonymised_queries_are_documented(self):
        self.assertIn("anonymised", self.guidance)

    def test_the_code_explains_itself_where_it_is_read(self):
        # A caveat only in the docs is a caveat the next maintainer will not see.
        self.assertIn("not additive", self.code)
        self.assertIn("support.google.com/webmasters", self.code)

    def test_the_summary_field_names_its_own_weighting(self):
        from seo_tools.gsc import summarise

        rows = [
            {"clicks": 10, "impressions": 1000, "position": 8.0},
            {"clicks": 1, "impressions": 10, "position": 40.0},
        ]
        out = summarise(rows)
        self.assertIn("avg_position_impression_weighted", out)
        # A naive mean would be 24.0; weighting keeps the big row dominant.
        self.assertLess(out["avg_position_impression_weighted"], 12)


class TestIndexNowIsScopedHonestly(unittest.TestCase):
    """The name promises Google. The protocol does not deliver it."""

    def setUp(self):
        self.skill = " ".join(
            (SKILLS_DIR / "indexation-check" / "SKILL.md").read_text(encoding="utf-8").split()
        )
        self.guidance = " ".join((DOCS_DIR / "source-of-record.md").read_text(encoding="utf-8").split())

    def test_the_skill_says_google_is_not_a_participant(self):
        self.assertIn("Google is not a participant", self.skill)

    def test_the_guidance_says_it_too(self):
        self.assertIn("Google is not a participant", self.guidance)

    def test_the_engines_it_does_reach_are_named(self):
        for engine in ("Bing", "Seznam", "Naver"):
            with self.subTest(engine=engine):
                self.assertIn(engine, self.skill)

    def test_it_is_not_offered_as_a_google_indexing_fix(self):
        self.assertIn("never as a fix for a Google indexing problem", self.skill)


class TestTheValidatorReadsCodeSpansAsCode(unittest.TestCase):
    """A URL path in backticks is not a reference to a skill.

    `/indexnow?url=` tripped the sibling-reference check, which would hit anyone
    documenting a URL. The fix has to stay precise: a real bad reference in prose
    must still be caught.
    """

    def test_a_url_path_in_a_code_span_is_ignored(self):
        import subprocess
        import sys

        root = AGENTS_DIR.parent
        result = subprocess.run(
            [sys.executable, str(root / "scripts" / "validate.py")],
            capture_output=True, text=True, cwd=str(root),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("which is not a skill in this repo", result.stdout)

    def test_the_check_still_exists_and_strips_both_forms(self):
        source = (AGENTS_DIR.parent / "scripts" / "validate.py").read_text(encoding="utf-8")
        self.assertIn("CODE_SPAN", source)
        self.assertIn("FENCE.sub", source)
        self.assertIn("CODE_SPAN.sub", source)
        self.assertIn("which is not a skill in this repo", source)


class TestBingCopilotDirectivesAreChecked(unittest.TestCase):
    """A page can be fully crawlable and still opted out of Copilot answers.

    Bing documents meta directives that decide what Copilot may use, separately
    from whether the page may be fetched. `noarchive` is the dangerous one: every
    robots.txt check passes while the page drops out of AI answers entirely.
    """

    def findings_for(self, content, headers=None):
        from seo_tools.audits import audit_page

        html = (
            '<html lang="en"><head><title>A title of a reasonable width for this</title>'
            '<meta name="robots" content="{}"></head>'
            "<body><h1>H</h1><p>x</p></body></html>"
        ).format(content)
        return {f["check"]: f for f in audit_page(parse_page(html, "https://e.com/"), headers)["findings"]}

    def test_noarchive_is_raised_as_a_warning(self):
        found = self.findings_for("index, follow, noarchive")
        self.assertIn("robots.noarchive", found)
        self.assertEqual(found["robots.noarchive"]["severity"], "warning")

    def test_nocache_is_raised_as_info(self):
        found = self.findings_for("index, follow, nocache")
        self.assertIn("robots.nocache", found)
        self.assertEqual(found["robots.nocache"]["severity"], "info")

    def test_the_finding_is_scoped_to_the_engine_that_documents_it(self):
        # Google publishes no equivalent, so stating it generally would be a claim
        # about Google that Google has not made.
        found = self.findings_for("noarchive")
        self.assertEqual(found["robots.noarchive"]["affects"], "Bing and Copilot")

    def test_the_header_form_is_caught_too(self):
        found = self.findings_for("index", headers={"x-robots-tag": "noarchive"})
        self.assertIn("robots.noarchive", found)

    def test_a_clean_page_raises_neither(self):
        found = self.findings_for("index, follow")
        self.assertNotIn("robots.noarchive", found)
        self.assertNotIn("robots.nocache", found)

    def test_noarchive_does_not_imply_noindex(self):
        # The whole point: indexable and uncitable at the same time.
        found = self.findings_for("index, follow, noarchive")
        self.assertNotIn("robots.noindex_meta", found)


class TestTheEngineDisagreementIsRecorded(unittest.TestCase):
    """Google says AI needs no special optimisation. Bing publishes a checklist.

    A pack serving both cannot quietly pick a side, and quoting one engine's
    position as the industry's is the error this guards.
    """

    def setUp(self):
        self.text = " ".join((DOCS_DIR / "source-of-record.md").read_text(encoding="utf-8").split())

    def test_both_positions_are_stated(self):
        self.assertIn("Google says there is nothing extra to do", self.text)
        self.assertIn("Bing publishes a grounding checklist", self.text)

    def test_the_doc_does_not_pick_a_winner(self):
        self.assertIn("Both can be true", self.text)

    def test_bing_specific_directives_are_documented(self):
        for directive in ("noarchive", "nocache", "data-snippet"):
            with self.subTest(directive=directive):
                self.assertIn(directive, self.text)

    def test_the_indexnow_streaming_correction_is_recorded(self):
        self.assertIn("streamed, not batched", self.text)

    def test_the_skill_says_stream_rather_than_batch(self):
        skill = " ".join(
            (SKILLS_DIR / "indexation-check" / "SKILL.md").read_text(encoding="utf-8").split()
        )
        self.assertIn("Submit as things change, not in nightly batches", skill)


class TestTheSourceOfRecordIsNotOnlyGoogle(unittest.TestCase):
    """The file was renamed because the name had stopped being true."""

    def setUp(self):
        self.path = DOCS_DIR / "source-of-record.md"
        self.text = self.path.read_text(encoding="utf-8")

    def test_the_old_name_is_gone(self):
        self.assertFalse((DOCS_DIR / "google-guidance.md").exists())
        self.assertTrue(self.path.exists())

    def test_every_operator_the_pack_cites_is_listed(self):
        for source in ("developers.google.com", "schema.org", "web.dev", "bing.com", "indexnow.org"):
            with self.subTest(source=source):
                self.assertIn(source, self.text)

    def test_nothing_still_points_at_the_old_path(self):
        root = DOCS_DIR.parent
        for name in ("AGENTS.md", "README.md"):
            with self.subTest(file=name):
                self.assertNotIn("google-guidance", (root / name).read_text(encoding="utf-8"))


class TestTheEaaIsCitedNotInterpreted(unittest.TestCase):
    """A legal claim in a public tool is a different risk from an SEO tip.

    The skill may say what the directive says, with article numbers, so a reader
    can check it. It may not tell a stranger whether they are required to comply,
    which is a question about their business that four markup checks cannot reach.
    """

    def setUp(self):
        self.text = (SKILLS_DIR / "accessibility-audit" / "SKILL.md").read_text(encoding="utf-8")
        self.flat = " ".join(self.text.split())

    def test_it_refuses_to_decide_applicability(self):
        self.assertIn("this skill does not answer", self.flat.lower())

    def test_the_guardrail_forbids_a_compliance_verdict(self):
        self.assertIn("Never state that a site is or is not legally required to comply", self.text)

    def test_it_cites_the_primary_source(self):
        self.assertIn("eur-lex.europa.eu", self.text)
        self.assertIn("2019/882", self.text)

    def test_article_numbers_are_given_so_a_reader_can_check(self):
        for article in ("Article 2(2)", "Article 3(23)", "Article 4(5)", "Article 14", "Article 32"):
            with self.subTest(article=article):
                self.assertIn(article, self.text)

    def test_the_consumer_scope_is_stated(self):
        # Reading Article 2(2) as "all websites" is the common error, and for a
        # B2B pack it is the difference between in scope and out of it.
        self.assertIn("to consumers", self.flat)
        self.assertIn("consumer contract", self.flat)

    def test_the_microenterprise_test_is_stated_in_full(self):
        # Headcount alone is not the test, and the summaries that say so are wrong.
        self.assertIn("fewer than 10 persons", self.flat)
        self.assertIn("EUR 2 million", self.flat)

    def test_it_says_national_law_is_the_binding_text(self):
        self.assertIn("It is a directive", self.flat)

    def test_no_skill_claims_accessibility_is_a_ranking_factor(self):
        for path in sorted(SKILLS_DIR.rglob("SKILL.md")):
            flat = " ".join(path.read_text(encoding="utf-8").split()).lower()
            with self.subTest(skill=path.parent.name):
                self.assertNotIn("accessibility improves ranking", flat.replace("never claim accessibility improves ranking", ""))


class TestNoUnsubstitutedPlaceholdersShip(unittest.TestCase):
    """A template placeholder that survived into the file is a dead link or worse.

    Caught for real: the EAA section shipped `([EUR-Lex]({EUR}))` because the
    authoring script defined the URL and never substituted it. The skill validated,
    the suite passed, and the reader would have got a broken link to the one source
    that mattered most in that section.
    """

    # Placeholder shapes used by the scripts that generate these files. Angle
    # brackets are excluded on purpose: `<url>` and `<pack_root>` are real
    # documentation conventions here, not accidents.
    PLACEHOLDER = re.compile(r"\{[A-Z][A-Z0-9_]*\}")

    def test_no_prose_file_carries_one(self):
        docs = sorted(DOCS_DIR.glob("*.md"))
        for path in _prose_files() + docs:
            text = path.read_text(encoding="utf-8")
            for match in self.PLACEHOLDER.finditer(text):
                line = text[: match.start()].count("\n") + 1
                with self.subTest(file=path.name, line=line):
                    self.fail(
                        "{}:{} ships an unsubstituted placeholder {}".format(
                            path.name, line, match.group(0)
                        )
                    )

    def test_the_check_would_catch_a_planted_one(self):
        self.assertRegex("see ([Source]({EUR}))", self.PLACEHOLDER)
        self.assertNotRegex("run `python <pack_root>/seo.py`", self.PLACEHOLDER)


class TestTheReadmeDescribesTheActualRepo(unittest.TestCase):
    """The README is the first thing anyone reads and nothing was checking it.

    It claimed twenty-seven skills when there were twenty-eight, and 140 tests when
    there were 375. Both drifted silently over several releases. A pack whose whole
    argument is "cite it or do not claim it" should hold its own front page to that.
    """

    NUMBER_WORDS = {
        "Twenty-five": 25, "Twenty-six": 26, "Twenty-seven": 27, "Twenty-eight": 28,
        "Twenty-nine": 29, "Thirty": 30, "Thirty-one": 31, "Thirty-two": 32,
    }

    def setUp(self):
        self.root = AGENTS_DIR.parent
        self.readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.skills = sorted(d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").exists())

    def test_the_spelled_out_skill_count_is_right(self):
        claimed = [w for w in self.NUMBER_WORDS if "{} skills".format(w) in self.readme]
        self.assertEqual(len(claimed), 1, "expected exactly one spelled-out skill count")
        self.assertEqual(
            self.NUMBER_WORDS[claimed[0]], len(self.skills),
            "README says {} skills, the repo has {}".format(claimed[0], len(self.skills)),
        )

    def test_every_skill_has_a_catalogue_entry(self):
        for name in self.skills:
            with self.subTest(skill=name):
                self.assertIn("`/{}`".format(name), self.readme,
                              "{} is not in the README catalogue".format(name))

    def test_every_skill_has_a_support_matrix_row(self):
        for name in self.skills:
            with self.subTest(skill=name):
                self.assertRegex(
                    self.readme, r"\|\s*" + re.escape(name) + r"\s*\|",
                    "{} has no support matrix row".format(name),
                )

    def test_every_agent_is_named(self):
        for path in sorted(AGENTS_DIR.glob("*.md")):
            with self.subTest(agent=path.stem):
                self.assertIn("`{}`".format(path.stem), self.readme)

    def test_the_command_count_is_right(self):
        from seo_tools.cli import build_parser

        # Read the subparser choices, which is the same list --help prints, so the
        # README cannot drift from the commands that actually exist.
        actions = [a for a in build_parser()._actions if getattr(a, "dest", "") == "command"]
        self.assertEqual(len(actions), 1, "expected one subcommand group")
        actual = len(actions[0].choices)
        words = {"Twelve": 12, "Thirteen": 13, "Fourteen": 14, "Fifteen": 15, "Sixteen": 16}
        claimed = [w for w in words if "{} commands".format(w) in self.readme]
        self.assertEqual(len(claimed), 1, "expected exactly one spelled-out command count")
        self.assertEqual(words[claimed[0]], actual)

    def test_the_test_count_is_not_badly_stale(self):
        """Deliberately a tolerance, not an equality.

        Pinning it exactly would mean every new test breaks the README, which
        trains people to edit the number without reading the sentence. This
        catches the failure that actually happened: a count left behind for
        several releases.
        """
        claimed = [int(m) for m in re.findall(r"\*\* (\d{2,4}) tests,", self.readme)]
        self.assertEqual(len(claimed), 1, "expected exactly one test-count claim")
        loader = unittest.TestLoader()
        actual = loader.discover(str(self.root / "tests"), top_level_dir=str(self.root)).countTestCases()
        self.assertGreaterEqual(
            claimed[0], actual * 0.8,
            "README claims {} tests, the suite has {}".format(claimed[0], actual),
        )
        self.assertLessEqual(
            claimed[0], actual,
            "README claims {} tests, more than the {} that exist".format(claimed[0], actual),
        )


class TestPlatformConstraintsAreDocumented(unittest.TestCase):
    """A recommendation the platform cannot execute is homework, not a fix.

    The profile has recorded CMS / platform since the beginning and nothing read
    it, so every brief gave the same generic instruction regardless of whether the
    site could follow it.
    """

    PLATFORMS = ("WordPress", "Webflow", "Framer", "Lovable")

    def setUp(self):
        self.doc = (DOCS_DIR / "platforms.md").read_text(encoding="utf-8")
        self.flat = " ".join(self.doc.split())

    def test_the_reference_exists_and_covers_each_platform(self):
        for name in self.PLATFORMS:
            with self.subTest(platform=name):
                self.assertIn("## " + name, self.doc)

    def test_it_is_dated_because_platforms_ship_changes(self):
        self.assertIn("Checked 2026-", self.doc)

    def test_the_wordpress_plugin_dependency_is_stated_first(self):
        # Capability there is decided by which plugin is installed, and the
        # instruction differs per plugin, so asking comes before writing.
        self.assertIn("Ask which SEO plugin is installed before writing anything", self.flat)

    def test_the_webflow_localised_redirect_trap_is_recorded(self):
        self.assertIn("do not apply to localised", self.flat)

    def test_the_lovable_verified_crawler_behaviour_is_recorded(self):
        self.assertIn("Pre-rendering serves verified crawlers only", self.flat)

    def test_the_soft_404_at_scale_case_is_recorded(self):
        # Found on a real site: 22 of 31 sitemap URLs rendered the app's own 404
        # while answering HTTP 200.
        self.assertIn("advertise pages the app does not have", self.flat)


class TestTheRenderingFindingAdmitsItsBlindSpot(unittest.TestCase):
    """`requires_js` describes what this fetcher saw, not what Googlebot sees.

    Some hosts pre-render for verified crawlers only. Reporting a critical
    rendering defect from our fetch alone would be a confident claim about an
    engine we never observed.
    """

    def setUp(self):
        from seo_tools.audits import audit_page

        shell = "<html><head><title>T</title></head><body><div id=root></div></body></html>"
        self.finding = [
            f for f in audit_page(parse_page(shell, "https://e.com/"))["findings"]
            if f["check"] == "rendering.requires_js"
        ][0]

    def test_it_tells_the_reader_to_confirm(self):
        self.assertIn("confirm_with", self.finding)

    def test_the_message_names_the_false_positive_path(self):
        self.assertIn("pre-render for verified crawlers only", str(self.finding["message"]))

    def test_it_does_not_claim_googlebot_sees_a_shell(self):
        message = str(self.finding["message"])
        self.assertIn("does not prove Googlebot sees a shell", message)

    def test_it_is_still_a_warning_not_a_critical(self):
        # Real for fetchers outside the verified list, unproven for the rest.
        self.assertEqual(self.finding["severity"], "warning")


class TestBriefsAccountForThePlatform(unittest.TestCase):
    def test_the_agent_takes_platform_as_an_input(self):
        text = (AGENTS_DIR / "seo-brief-writer.md").read_text(encoding="utf-8")
        self.assertIn("| `platform` |", text)
        self.assertIn('"platform"', text)

    def test_the_agent_is_told_to_name_the_surface(self):
        flat = " ".join((AGENTS_DIR / "seo-brief-writer.md").read_text(encoding="utf-8").split())
        self.assertIn("Name the surface, not the outcome", flat)
        self.assertIn("Say who owns the change", flat)

    def test_the_skill_carries_the_same_step(self):
        flat = " ".join((SKILLS_DIR / "content-brief" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("platform's own vocabulary", flat)

    def test_the_brief_template_shows_the_platform(self):
        for path in (
            AGENTS_DIR / "seo-brief-writer.md",
            SKILLS_DIR / "content-brief" / "SKILL.md",
        ):
            with self.subTest(file=path.name):
                self.assertIn("Platform:", path.read_text(encoding="utf-8"))

    def test_the_newest_platforms_reached_the_technical_audit_table(self):
        # It already covered Webflow, HubSpot and WordPress. Framer and Lovable
        # were the gap, and Lovable is the one with the invisible failure mode.
        flat = " ".join((SKILLS_DIR / "technical-audit" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("| Framer |", flat)
        self.assertIn("| Lovable |", flat)
        self.assertIn("docs/platforms.md", flat)


if __name__ == "__main__":
    unittest.main()
