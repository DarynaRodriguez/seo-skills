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
        self.path = DOCS_DIR / "google-guidance.md"
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

    def test_every_google_looking_link_is_a_real_search_central_path(self):
        for path in _prose_files() + [DOCS_DIR / "google-guidance.md"]:
            for url in self.CITE.findall(path.read_text(encoding="utf-8")):
                if "google.com" not in url:
                    continue
                with self.subTest(file=path.name, url=url):
                    self.assertTrue(
                        url.startswith("https://developers.google.com/search/"),
                        "{} cites {} as Google guidance, which is not Search Central".format(path.name, url),
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
        text = (DOCS_DIR / "google-guidance.md").read_text(encoding="utf-8")
        self.assertIn("schema.org/docs/datamodel.html", text)
        self.assertIn("sd-policies", text)
        self.assertIn("only one of them draws lines", text)


if __name__ == "__main__":
    unittest.main()
