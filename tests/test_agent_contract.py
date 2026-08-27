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


if __name__ == "__main__":
    unittest.main()
