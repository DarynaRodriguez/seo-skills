"""robots.txt matching. The reason this exists instead of urllib.robotparser.

RFC 9309 cases: most specific group wins, then longest match, then allow on a
tie. Wildcards and end anchors. Getting any of these wrong means telling
someone GPTBot is allowed when it is not.
"""
import unittest

from seo_tools.robots import AI_AGENTS, RobotsTxt, robots_url_for

SAMPLE = """
# comments are ignored
User-agent: *
Disallow: /private/
Allow: /private/public-bit/
Disallow: /*.pdf$
Crawl-delay: 10

User-agent: GPTBot
Disallow: /

User-agent: Googlebot
User-agent: Bingbot
Disallow: /internal/

Sitemap: https://example.com/sitemap.xml
Sitemap: /relative-sitemap.xml
"""


class TestGroupSelection(unittest.TestCase):
    def setUp(self):
        self.robots = RobotsTxt(SAMPLE, 200, url="https://example.com/robots.txt")

    def test_a_named_group_beats_the_wildcard(self):
        verdict = self.robots.can_fetch("GPTBot", "https://example.com/anything")
        self.assertFalse(verdict["allowed"])
        self.assertEqual(verdict["matched_group"], "gptbot")

    def test_an_unnamed_agent_falls_back_to_the_wildcard(self):
        verdict = self.robots.can_fetch("SomeRandomBot", "https://example.com/private/x")
        self.assertFalse(verdict["allowed"])
        self.assertEqual(verdict["matched_group"], "*")

    def test_stacked_user_agent_lines_share_one_group(self):
        for agent in ("Googlebot", "Bingbot"):
            with self.subTest(agent=agent):
                verdict = self.robots.can_fetch(agent, "https://example.com/internal/x")
                self.assertFalse(verdict["allowed"])

    def test_a_stacked_group_does_not_inherit_the_wildcard_rules(self):
        # Googlebot has its own group, so the wildcard Disallow: /private/ does
        # not apply to it. This is the rule most home-made parsers get wrong.
        verdict = self.robots.can_fetch("Googlebot", "https://example.com/private/x")
        self.assertTrue(verdict["allowed"])


class TestLongestMatch(unittest.TestCase):
    def setUp(self):
        self.robots = RobotsTxt(SAMPLE, 200)

    def test_a_longer_allow_beats_a_shorter_disallow(self):
        verdict = self.robots.can_fetch("AnyBot", "https://example.com/private/public-bit/page")
        self.assertTrue(verdict["allowed"])
        self.assertIn("public-bit", str(verdict["matched_rule"]))

    def test_the_shorter_disallow_still_covers_its_siblings(self):
        self.assertFalse(
            self.robots.can_fetch("AnyBot", "https://example.com/private/secret")["allowed"]
        )

    def test_equal_length_ties_go_to_allow(self):
        robots = RobotsTxt("User-agent: *\nDisallow: /x\nAllow: /x\n", 200)
        self.assertTrue(robots.can_fetch("AnyBot", "https://example.com/x")["allowed"])


class TestPatterns(unittest.TestCase):
    def setUp(self):
        self.robots = RobotsTxt(SAMPLE, 200)

    def test_wildcard_and_end_anchor(self):
        self.assertFalse(self.robots.can_fetch("AnyBot", "https://example.com/docs/file.pdf")["allowed"])

    def test_the_anchor_means_the_extension_must_end_the_path(self):
        self.assertTrue(
            self.robots.can_fetch("AnyBot", "https://example.com/file.pdf.html")["allowed"]
        )

    def test_query_strings_are_part_of_the_path_for_matching(self):
        robots = RobotsTxt("User-agent: *\nDisallow: /*?sort=\n", 200)
        self.assertFalse(
            robots.can_fetch("AnyBot", "https://example.com/list?sort=price")["allowed"]
        )
        self.assertTrue(robots.can_fetch("AnyBot", "https://example.com/list")["allowed"])


class TestStatusHandling(unittest.TestCase):
    def test_401_and_403_mean_disallow_everything(self):
        for status in (401, 403):
            with self.subTest(status=status):
                robots = RobotsTxt("", status)
                self.assertFalse(robots.can_fetch("GPTBot", "https://example.com/")["allowed"])

    def test_404_means_no_restrictions(self):
        self.assertTrue(RobotsTxt("", 404).can_fetch("GPTBot", "https://example.com/")["allowed"])

    def test_an_empty_file_allows_everything(self):
        self.assertTrue(RobotsTxt("", 200).can_fetch("GPTBot", "https://example.com/")["allowed"])

    def test_bare_disallow_with_no_path_allows_everything(self):
        robots = RobotsTxt("User-agent: *\nDisallow:\n", 200)
        self.assertTrue(robots.can_fetch("AnyBot", "https://example.com/anything")["allowed"])


class TestDirectives(unittest.TestCase):
    def setUp(self):
        self.robots = RobotsTxt(SAMPLE, 200, url="https://example.com/robots.txt")

    def test_relative_sitemaps_are_resolved(self):
        self.assertIn("https://example.com/relative-sitemap.xml", self.robots.sitemaps)

    def test_absolute_sitemaps_are_kept(self):
        self.assertIn("https://example.com/sitemap.xml", self.robots.sitemaps)

    def test_crawl_delay_is_captured_without_being_treated_as_a_rule(self):
        self.assertEqual(self.robots.crawl_delay.get("*"), "10")

    def test_rules_before_any_user_agent_are_reported_not_applied(self):
        robots = RobotsTxt("Disallow: /orphan\nUser-agent: *\nDisallow: /real\n", 200)
        self.assertTrue(robots.can_fetch("AnyBot", "https://example.com/orphan")["allowed"])
        self.assertIn("Disallow: /orphan", robots.unknown_directives)


class TestAiAudit(unittest.TestCase):
    def test_training_and_citation_blocks_are_reported_separately(self):
        robots = RobotsTxt(
            "User-agent: GPTBot\nDisallow: /\n\nUser-agent: PerplexityBot\nDisallow: /\n", 200
        )
        audit = robots.audit_ai_agents("https://example.com/pricing")
        self.assertIn("GPTBot", audit["blocked_training"])
        self.assertIn("PerplexityBot", audit["blocked_search_index"])
        self.assertEqual(audit["blocked_count"], 2)

    def test_every_agent_carries_a_cost_when_blocked(self):
        robots = RobotsTxt("User-agent: *\nDisallow: /\n", 200)
        audit = robots.audit_ai_agents("https://example.com/")
        self.assertEqual(audit["blocked_count"], len(AI_AGENTS))
        for row in audit["agents"]:
            with self.subTest(agent=row["agent"]):
                self.assertTrue(row["cost_of_blocking"])

    def test_google_extended_is_not_conflated_with_googlebot(self):
        # Blocking Google-Extended does not remove you from Search or AI
        # Overviews. Conflating the two is the most expensive mistake here.
        robots = RobotsTxt("User-agent: Google-Extended\nDisallow: /\n", 200)
        audit = robots.audit_ai_agents("https://example.com/")
        self.assertEqual(audit["blocked_count"], 1)
        allowed = {r["agent"]: r["allowed"] for r in audit["agents"]}
        self.assertFalse(allowed["Google-Extended"])
        self.assertTrue(allowed["Googlebot"])


class TestRobotsUrl(unittest.TestCase):
    def test_it_is_per_host_and_scheme_not_per_path(self):
        self.assertEqual(
            robots_url_for("https://example.com/deep/path?x=1"), "https://example.com/robots.txt"
        )

    def test_a_non_default_port_is_kept(self):
        self.assertEqual(
            robots_url_for("http://example.com:8080/x"), "http://example.com:8080/robots.txt"
        )


if __name__ == "__main__":
    unittest.main()
