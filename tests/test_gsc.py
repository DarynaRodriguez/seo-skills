"""Search Console CSV handling: the zero-cost path into real traffic data.

Covers the input variety this will actually meet: English and German headers,
comma and semicolon delimiters, percent CTR, comma decimals, a BOM, and the
UI exports that carry only one dimension.
"""
import tempfile
import unittest
from pathlib import Path

from seo_tools.gsc import (
    GscError,
    cannibalisation,
    compare_periods,
    ctr_outliers,
    load_csv,
    parse_number,
    striking_distance,
    summarise,
)

ENGLISH = (
    "Top queries,Clicks,Impressions,CTR,Position\n"
    "procurement software,120,4000,3%,4.2\n"
    "source to pay,15,3000,0.5%,12.4\n"
    "supplier management,0,900,0%,18.9\n"
)

GERMAN_SEMICOLON = (
    "Häufigste Suchanfragen;Klicks;Impressionen;Klickrate;Durchschnittliche Position\n"
    "beschaffungssoftware;120;4.000;3,0%;4,2\n"
    "lieferantenmanagement;15;3.000;0,5%;12,4\n"
)

QUERY_AND_PAGE = (
    "Query,Page,Clicks,Impressions,CTR,Position\n"
    "procurement software,https://e.com/a,100,3000,3.3%,4.1\n"
    "procurement software,https://e.com/b,20,2000,1%,8.7\n"
    "procurement software,https://e.com/c,1,50,2%,30.0\n"
    "unique term,https://e.com/d,50,1000,5%,3.0\n"
)

PAGES_BEFORE = (
    "Top pages,Clicks,Impressions,CTR,Position\n"
    "https://e.com/a,500,10000,5%,3.0\n"
    "https://e.com/b,200,5000,4%,6.0\n"
    "https://e.com/gone,100,2000,5%,4.0\n"
)
PAGES_NOW = (
    "Top pages,Clicks,Impressions,CTR,Position\n"
    "https://e.com/a,300,9500,3.2%,5.5\n"
    "https://e.com/b,240,5200,4.6%,5.5\n"
    "https://e.com/new,80,1500,5.3%,7.0\n"
)


def write(text, name="export.csv", encoding="utf-8"):
    directory = tempfile.mkdtemp()
    path = Path(directory) / name
    path.write_text(text, encoding=encoding)
    return str(path)


class TestNumberParsing(unittest.TestCase):
    def test_the_forms_a_real_export_contains(self):
        cases = {
            "120": 120.0,
            "4,000": 4000.0,
            "4.000": 4000.0,
            "3%": 0.03,
            "0,5%": 0.005,
            "4,2": 4.2,
            "1.234,56": 1234.56,
            "1,234.56": 1234.56,
            "": None,
            "-": None,
            "n/a": None,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_number(raw), expected)


class TestLoading(unittest.TestCase):
    def test_english_comma_export(self):
        loaded = load_csv(write(ENGLISH))
        self.assertEqual(loaded["row_count"], 3)
        self.assertIn("query", loaded["columns_detected"])
        self.assertEqual(loaded["rows"][0]["clicks"], 120.0)
        self.assertAlmostEqual(loaded["rows"][0]["ctr"], 0.03)

    def test_german_semicolon_export(self):
        loaded = load_csv(write(GERMAN_SEMICOLON))
        self.assertEqual(loaded["delimiter"], ";")
        self.assertEqual(loaded["rows"][0]["impressions"], 4000.0)
        self.assertEqual(loaded["rows"][0]["position"], 4.2)
        self.assertEqual(loaded["rows"][0]["query"], "beschaffungssoftware")

    def test_a_bom_does_not_become_part_of_the_first_header(self):
        loaded = load_csv(write(ENGLISH, encoding="utf-8-sig"))
        self.assertIn("query", loaded["columns_detected"])

    def test_ctr_is_derived_when_the_column_is_absent(self):
        loaded = load_csv(write("Page,Clicks,Impressions\nhttps://e.com/a,25,100\n"))
        self.assertAlmostEqual(loaded["rows"][0]["ctr"], 0.25)

    def test_unrecognised_columns_are_reported_not_silently_dropped(self):
        loaded = load_csv(write("Top pages,Clicks,Something Odd\nhttps://e.com/a,5,x\n"))
        self.assertEqual(loaded["columns_ignored"], ["Something Odd"])

    def test_a_missing_file_says_so(self):
        with self.assertRaises(GscError):
            load_csv("no-such-file.csv")

    def test_a_file_with_no_recognisable_columns_says_so(self):
        with self.assertRaises(GscError) as caught:
            load_csv(write("alpha,beta\n1,2\n"))
        self.assertIn("no recognisable columns", str(caught.exception))


class TestSummary(unittest.TestCase):
    def test_average_position_is_impression_weighted_not_a_plain_mean(self):
        rows = load_csv(write(ENGLISH))["rows"]
        summary = summarise(rows)
        self.assertEqual(summary["clicks"], 135)
        self.assertEqual(summary["impressions"], 7900)
        plain_mean = (4.2 + 12.4 + 18.9) / 3
        self.assertNotAlmostEqual(summary["avg_position_impression_weighted"], plain_mean, places=1)


class TestStrikingDistance(unittest.TestCase):
    def test_it_selects_the_band_and_orders_by_impressions(self):
        rows = load_csv(write(ENGLISH))["rows"]
        found = striking_distance(rows, min_impressions=100)
        self.assertEqual([r["query"] for r in found], ["source to pay", "supplier management"])

    def test_low_impression_rows_are_excluded(self):
        rows = load_csv(write(ENGLISH))["rows"]
        self.assertEqual(striking_distance(rows, min_impressions=5000), [])


class TestCtrOutliers(unittest.TestCase):
    def test_the_benchmark_is_the_dataset_itself(self):
        rows = load_csv(write(QUERY_AND_PAGE))["rows"]
        result = ctr_outliers(rows, min_impressions=10)
        self.assertIn("this export", result["benchmark"])

    def test_a_band_with_too_few_rows_produces_no_median_and_no_findings(self):
        rows = load_csv(write(ENGLISH))["rows"]
        self.assertEqual(ctr_outliers(rows, min_impressions=100)["findings"], [])


class TestCannibalisation(unittest.TestCase):
    def test_it_groups_competing_pages_for_one_query(self):
        rows = load_csv(write(QUERY_AND_PAGE))["rows"]
        result = cannibalisation(rows, min_impressions=100, min_share=0.1)
        self.assertTrue(result["supported"])
        self.assertEqual(result["group_count"], 1)
        group = result["groups"][0]
        self.assertEqual(group["query"], "procurement software")
        # /c holds under 10 percent of impressions, so it is not a competitor.
        self.assertEqual(group["pages_competing"], 2)

    def test_a_query_with_one_page_is_not_a_group(self):
        rows = load_csv(write(QUERY_AND_PAGE))["rows"]
        queries = {g["query"] for g in cannibalisation(rows, min_impressions=100)["groups"]}
        self.assertNotIn("unique term", queries)

    def test_a_queries_only_export_says_what_is_missing_instead_of_guessing(self):
        rows = load_csv(write(ENGLISH))["rows"]
        result = cannibalisation(rows)
        self.assertFalse(result["supported"])
        self.assertIn("queries only", result["note"])
        self.assertEqual(result["groups"], [])


class TestPeriodComparison(unittest.TestCase):
    def setUp(self):
        self.now = load_csv(write(PAGES_NOW, "now.csv"))["rows"]
        self.before = load_csv(write(PAGES_BEFORE, "before.csv"))["rows"]

    def test_losses_are_ranked_by_clicks_lost(self):
        result = compare_periods(self.now, self.before, dimension="page", min_impressions=100)
        self.assertTrue(result["supported"])
        self.assertEqual(result["biggest_losses"][0]["page"], "https://e.com/a")
        self.assertEqual(result["biggest_losses"][0]["clicks_delta"], -200)

    def test_a_page_that_disappeared_is_marked_gone(self):
        result = compare_periods(self.now, self.before, dimension="page", min_impressions=100)
        self.assertEqual([r["page"] for r in result["lost_entirely"]], ["https://e.com/gone"])

    def test_gains_are_separated_from_losses(self):
        result = compare_periods(self.now, self.before, dimension="page", min_impressions=100)
        gains = {row["page"]: row["clicks_delta"] for row in result["biggest_gains"]}
        # A page that did not exist before is a real gain, and 80 beats 40, so
        # the new page leads. Both are gains; neither appears in the losses.
        self.assertEqual(gains, {"https://e.com/new": 80, "https://e.com/b": 40})
        self.assertEqual(result["biggest_gains"][0]["page"], "https://e.com/new")
        self.assertNotIn("https://e.com/b", {row["page"] for row in result["biggest_losses"]})

    def test_a_page_that_is_new_is_marked_new(self):
        result = compare_periods(self.now, self.before, dimension="page", min_impressions=100)
        statuses = {row["page"]: row["status"] for row in result["biggest_gains"]}
        self.assertEqual(statuses["https://e.com/new"], "new")

    def test_the_period_assumption_is_stated_rather_than_hidden(self):
        result = compare_periods(self.now, self.before, dimension="page")
        self.assertIn("equal-length, non-overlapping", result["caveat"])

    def test_joining_on_a_dimension_neither_file_has_is_refused(self):
        result = compare_periods(self.now, self.before, dimension="query")
        self.assertFalse(result["supported"])


if __name__ == "__main__":
    unittest.main()
