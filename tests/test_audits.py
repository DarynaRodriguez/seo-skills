"""Pixel measurement and the on-page rules built on top of it."""
import unittest

from seo_tools import typography
from seo_tools.audits import audit_page, check_headings, check_meta, check_schema
from seo_tools.parsing import parse_page


def checks(findings):
    return {f["check"] for f in findings}


class TestTypography(unittest.TestCase):
    def test_equal_character_counts_can_have_very_different_widths(self):
        # The whole reason this module exists.
        narrow = typography.measure_px("illillillill", typography.TITLE_FONT_PX)
        wide = typography.measure_px("WMWMWMWMWMWM", typography.TITLE_FONT_PX)
        self.assertEqual(len("illillillill"), len("WMWMWMWMWMWM"))
        self.assertGreater(wide, narrow * 3)

    def test_empty_text_is_zero(self):
        self.assertEqual(typography.measure_px("", 20), 0.0)

    def test_untabulated_characters_fall_back_rather_than_crash(self):
        self.assertGreater(typography.measure_px("emoji \U0001f600 and 中文", 20), 0)

    def test_a_short_title_does_not_truncate(self):
        measured = typography.measure_title("Pricing")
        self.assertFalse(measured["truncates"])
        self.assertEqual(measured["truncated_preview"], "Pricing")

    def test_a_long_title_truncates_on_a_word_boundary(self):
        long_title = "Procurement software for mid market manufacturers across Europe and beyond"
        measured = typography.measure_title(long_title)
        self.assertTrue(measured["truncates"])
        preview = measured["truncated_preview"]
        self.assertTrue(preview.endswith("…"))
        self.assertLess(len(preview), len(long_title))
        # The cut lands between words, so no half-word survives.
        self.assertIn(preview[:-1].strip().split()[-1], long_title.split())

    def test_the_preview_fits_the_budget_it_claims(self):
        measured = typography.measure_title("A" * 200)
        self.assertLessEqual(
            typography.measure_px(measured["truncated_preview"], typography.TITLE_FONT_PX),
            typography.TITLE_LIMIT_PX,
        )

    def test_every_measurement_carries_its_method(self):
        for measured in (typography.measure_title("x"), typography.measure_description("y")):
            self.assertIn("Estimate", measured["method"])


class TestMetaRules(unittest.TestCase):
    def test_a_missing_title_is_critical(self):
        findings = check_meta({"title": None, "meta_description": "x" * 100, "h1": []})
        self.assertIn("title.missing", checks(findings))
        self.assertEqual(
            [f["severity"] for f in findings if f["check"] == "title.missing"], ["critical"]
        )

    def test_a_missing_description_is_a_warning_not_a_crisis(self):
        findings = check_meta({"title": "A sensible title of about forty chars", "meta_description": None, "h1": []})
        self.assertIn("description.missing", checks(findings))
        self.assertEqual(
            [f["severity"] for f in findings if f["check"] == "description.missing"], ["warning"]
        )

    def test_an_empty_description_is_distinguished_from_a_missing_one(self):
        findings = check_meta({"title": "A sensible title of about forty chars", "meta_description": "", "h1": []})
        self.assertIn("description.empty", checks(findings))
        self.assertNotIn("description.missing", checks(findings))

    def test_a_wide_title_is_flagged_with_the_evidence(self):
        findings = check_meta(
            {"title": "W" * 60, "meta_description": "x" * 100, "h1": []}
        )
        finding = [f for f in findings if f["check"] == "title.too_wide"][0]
        self.assertIn("px", finding)
        self.assertIn("preview", finding)
        self.assertIn("Estimate", finding["method"])

    def test_a_title_identical_to_the_h1_is_only_info(self):
        findings = check_meta(
            {"title": "Same words here", "meta_description": "x" * 100, "h1": ["Same words here"]}
        )
        finding = [f for f in findings if f["check"] == "title.duplicates_h1"][0]
        self.assertEqual(finding["severity"], "info")

    def test_a_good_pair_produces_nothing(self):
        findings = check_meta(
            {
                "title": "Procurement software for manufacturers",
                "meta_description": (
                    "Automate sourcing, manage suppliers and keep contracts in one place. "
                    "Built for mid market teams."
                ),
                "h1": ["Something different"],
            }
        )
        self.assertEqual(findings, [])


class TestHeadingRules(unittest.TestCase):
    def test_no_h1_is_critical(self):
        self.assertIn("h1.missing", checks(check_headings({"h1": [], "headings": []})))

    def test_several_h1s_is_a_warning(self):
        findings = check_headings(
            {"h1": ["One", "Two"], "headings": [{"level": 1, "text": "One"}, {"level": 1, "text": "Two"}]}
        )
        self.assertIn("h1.multiple", checks(findings))

    def test_a_skipped_level_is_info(self):
        findings = check_headings(
            {"h1": ["Title"], "headings": [{"level": 1, "text": "Title"}, {"level": 3, "text": "Sub"}]}
        )
        finding = [f for f in findings if f["check"] == "heading.level_skipped"][0]
        self.assertEqual(finding["severity"], "info")
        self.assertEqual((finding["previous_level"], finding["level"]), (1, 3))

    def test_an_empty_heading_is_reported(self):
        findings = check_headings({"h1": ["A"], "headings": [{"level": 1, "text": "A"}, {"level": 2, "text": "  "}]})
        self.assertIn("heading.empty", checks(findings))

    def test_a_clean_outline_produces_nothing(self):
        findings = check_headings(
            {
                "h1": ["Title"],
                "headings": [
                    {"level": 1, "text": "Title"},
                    {"level": 2, "text": "Section"},
                    {"level": 3, "text": "Detail"},
                    {"level": 2, "text": "Another"},
                ],
            }
        )
        self.assertEqual(findings, [])


class TestSchemaRules(unittest.TestCase):
    def test_broken_json_is_critical_because_engines_ignore_it_silently(self):
        page = parse_page('<script type="application/ld+json">{oops}</script>', "https://e.com/")
        finding = [f for f in check_schema(page) if f["check"] == "schema.invalid_json"][0]
        self.assertEqual(finding["severity"], "critical")

    def test_a_missing_required_property_is_named(self):
        page = parse_page(
            '<script type="application/ld+json">{"@type":"Product","description":"x"}</script>',
            "https://e.com/",
        )
        finding = [f for f in check_schema(page) if f["check"] == "schema.missing_required"][0]
        self.assertEqual(finding["property"], "name")
        self.assertEqual(finding["type"], "Product")

    def test_a_retired_rich_result_type_is_called_out(self):
        page = parse_page(
            '<script type="application/ld+json">{"@type":"HowTo","name":"x","step":[]}</script>',
            "https://e.com/",
        )
        finding = [f for f in check_schema(page) if f["check"] == "schema.no_rich_result"][0]
        self.assertIn("HowTo", finding["message"])

    def test_valid_complete_schema_produces_no_warnings(self):
        page = parse_page(
            '<script type="application/ld+json">{"@type":"Organization","name":"Acme"}</script>',
            "https://e.com/",
        )
        self.assertEqual(
            [f for f in check_schema(page) if f["severity"] != "info"], []
        )


class TestFullAudit(unittest.TestCase):
    def test_findings_come_back_worst_first(self):
        page = parse_page("<html><body><div id='root'></div></body></html>", "https://e.com/")
        page["status"] = 200
        result = audit_page(page)
        severities = [f["severity"] for f in result["findings"]]
        self.assertEqual(severities, sorted(severities, key=lambda s: {"critical": 0, "warning": 1, "info": 2}[s]))

    def test_counts_match_the_findings(self):
        page = parse_page("<html><body></body></html>", "https://e.com/")
        result = audit_page(page)
        self.assertEqual(sum(result["counts"].values()), result["total"])
        self.assertEqual(result["total"], len(result["findings"]))

    def test_a_noindex_header_is_caught_even_though_it_is_not_in_the_html(self):
        page = parse_page("<html><head><title>T</title></head><body></body></html>", "https://e.com/")
        result = audit_page(page, {"x-robots-tag": "noindex, nofollow"})
        self.assertIn("robots.noindex_header", checks(result["findings"]))


if __name__ == "__main__":
    unittest.main()
