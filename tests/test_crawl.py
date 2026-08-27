"""Crawl export ingestion. The point is that the provider is interchangeable.

Screaming Frog, Sitebulb and a hand-built spreadsheet all describe the same
thing, so all three must land on one row shape and produce the same findings.
"""
import pathlib
import tempfile
import unittest

from seo_tools.crawl import (
    CANONICAL_FIELDS,
    CrawlError,
    analyse,
    broken,
    detect_exporter,
    duplicates,
    load_crawl,
    missing,
    non_self_canonical,
    orphans,
    redirect_chains,
    summarise,
    thin,
)

SCREAMING_FROG = """Address,Content Type,Status Code,Status,Indexability,Indexability Status,Title 1,Meta Description 1,H1-1,Meta Robots 1,Canonical Link Element 1,Word Count,Crawl Depth,Inlinks,Outlinks,Redirect URL
https://example.com/,text/html,200,OK,Indexable,,Procurement software,A clear description here,Procurement software,index follow,https://example.com/,850,0,120,45,
https://example.com/pricing,text/html,200,OK,Indexable,,Procurement software,Pricing described here,Pricing,index follow,https://example.com/pricing,410,1,30,22,
https://example.com/thin,text/html,200,OK,Indexable,,Thin page,,,,https://example.com/thin,90,3,2,4,
https://example.com/orphan,text/html,200,OK,Indexable,,Orphaned page,Has a description,Orphan,index follow,https://example.com/orphan,600,4,0,3,
https://example.com/variant,text/html,200,OK,Non-Indexable,Canonicalised,Variant,A variant page,Variant,index follow,https://example.com/pricing,400,2,5,20,
https://example.com/old,text/html,301,Moved Permanently,Non-Indexable,Redirected,,,,,,0,2,8,0,https://example.com/middle
https://example.com/middle,text/html,301,Moved Permanently,Non-Indexable,Redirected,,,,,,0,3,1,0,https://example.com/pricing
https://example.com/gone,text/html,404,Not Found,Non-Indexable,Client Error,,,,,,0,2,14,0,
https://example.com/thank-you,text/html,200,OK,Non-Indexable,noindex,Procurement software,,,noindex follow,https://example.com/thank-you,120,2,3,2,
"""

SITEBULB = """URL;HTTP Status Code;Indexable;Page Title;Meta Description;First H1;Crawl Depth;Internal Inlinks;Word Count;Canonical URL
https://example.org/;200;Yes;Home;A description;Home;0;90;700;https://example.org/
https://example.org/a;200;Yes;Same Title;Another description;A;1;12;250;https://example.org/a
https://example.org/b;200;Yes;Same Title;Another description;B;1;9;240;https://example.org/b
https://example.org/dead;410;No;;;;2;5;0;
"""


def write(text, name="crawl.csv", encoding="utf-8"):
    path = pathlib.Path(tempfile.mkdtemp()) / name
    path.write_text(text, encoding=encoding)
    return str(path)


class TestLoading(unittest.TestCase):
    def test_screaming_frog_export(self):
        loaded = load_crawl(write(SCREAMING_FROG))
        self.assertEqual(loaded["exporter"], "Screaming Frog")
        self.assertEqual(loaded["row_count"], 9)
        for field in ("url", "status", "title", "canonical", "word_count", "inlinks"):
            self.assertIn(field, loaded["columns_detected"])

    def test_sitebulb_export_with_different_names_and_delimiter(self):
        loaded = load_crawl(write(SITEBULB))
        self.assertEqual(loaded["delimiter"], ";")
        self.assertEqual(loaded["row_count"], 4)
        self.assertIn("url", loaded["columns_detected"])
        self.assertIn("title", loaded["columns_detected"])

    def test_a_bom_does_not_break_the_first_column(self):
        loaded = load_crawl(write(SCREAMING_FROG, encoding="utf-8-sig"))
        self.assertIn("url", loaded["columns_detected"])
        self.assertEqual(loaded["rows"][0]["url"], "https://example.com/")

    def test_every_row_carries_every_canonical_field(self):
        # Downstream code reads these unconditionally, so absence must be None
        # rather than a missing key.
        for row in load_crawl(write(SITEBULB))["rows"]:
            self.assertEqual(set(row), set(CANONICAL_FIELDS))

    def test_numbers_are_parsed_not_left_as_text(self):
        row = load_crawl(write(SCREAMING_FROG))["rows"][0]
        self.assertEqual(row["status"], 200)
        self.assertEqual(row["word_count"], 850)
        self.assertEqual(row["inlinks"], 120)
        self.assertEqual(row["crawl_depth"], 0)

    def test_indexability_becomes_a_boolean_from_either_vocabulary(self):
        frog = {r["url"]: r for r in load_crawl(write(SCREAMING_FROG))["rows"]}
        bulb = {r["url"]: r for r in load_crawl(write(SITEBULB))["rows"]}
        self.assertIs(frog["https://example.com/"]["indexability"], True)
        self.assertIs(frog["https://example.com/gone"]["indexability"], False)
        self.assertIs(bulb["https://example.org/"]["indexability"], True)
        self.assertIs(bulb["https://example.org/dead"]["indexability"], False)

    def test_a_file_with_no_url_column_is_refused_with_the_fix(self):
        with self.assertRaises(CrawlError) as caught:
            load_crawl(write("Col1,Col2\n1,2\n"))
        self.assertIn("--columns", str(caught.exception))

    def test_a_missing_file_says_so(self):
        with self.assertRaises(CrawlError):
            load_crawl("no-such-crawl.csv")

    def test_unrecognised_columns_are_reported_not_dropped_silently(self):
        loaded = load_crawl(write("Address,Status Code,Something Odd\nhttps://e.com/,200,x\n"))
        self.assertEqual(loaded["columns_ignored"], ["Something Odd"])


class TestColumnOverride(unittest.TestCase):
    def test_it_reads_an_exporter_nobody_has_heard_of(self):
        loaded = load_crawl(
            write("A,B,C\nhttps://example.net/,200,A title\n"), columns="url,status,title"
        )
        self.assertEqual(loaded["columns_resolved_by"], "the --columns override")
        self.assertEqual(loaded["rows"][0]["title"], "A title")

    def test_a_dash_skips_a_column(self):
        loaded = load_crawl(
            write("A,B,C\nhttps://example.net/,junk,A title\n"), columns="url,-,title"
        )
        self.assertIsNone(loaded["rows"][0]["status"])
        self.assertEqual(loaded["rows"][0]["title"], "A title")

    def test_an_unknown_field_name_is_refused(self):
        with self.assertRaises(CrawlError) as caught:
            load_crawl(write("A,B\nhttps://e.com/,x\n"), columns="url,sessions")
        self.assertIn("sessions", str(caught.exception))


class TestAnalyses(unittest.TestCase):
    def setUp(self):
        self.rows = load_crawl(write(SCREAMING_FROG))["rows"]

    def test_summary_bands_statuses_rather_than_listing_codes(self):
        summary = summarise(self.rows)
        self.assertEqual(summary["urls"], 9)
        self.assertEqual(summary["by_status_band"], {"2xx": 6, "3xx": 2, "4xx": 1})
        self.assertEqual(summary["indexable"], 4)
        self.assertEqual(summary["max_crawl_depth"], 4)

    def test_a_noindexed_page_is_not_a_duplicate(self):
        # /thank-you shares its title with the homepage but is noindexed, so it
        # is not competing with anything and must not be reported.
        groups = duplicates(self.rows, "title")
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["count"], 2)
        self.assertNotIn("https://example.com/thank-you", groups[0]["urls"])

    def test_missing_fields_only_count_indexable_pages(self):
        # Redirects and 404s have no title by definition. Counting them would
        # bury the one indexable page that genuinely lacks a description.
        self.assertEqual(missing(self.rows, "title"), [])
        self.assertEqual(missing(self.rows, "meta_description"), ["https://example.com/thin"])

    def test_orphans_are_indexable_pages_with_no_inlinks(self):
        self.assertEqual(orphans(self.rows), ["https://example.com/orphan"])

    def test_thin_pages_are_listed_shallowest_first_and_the_threshold_is_an_argument(self):
        self.assertEqual([r["url"] for r in thin(self.rows)], ["https://example.com/thin"])
        self.assertEqual(len(thin(self.rows, threshold=500)), 2)
        self.assertEqual(thin(self.rows, threshold=10), [])

    def test_a_canonical_pointing_elsewhere_is_found(self):
        found = non_self_canonical(self.rows)
        self.assertEqual([r["url"] for r in found], ["https://example.com/variant"])
        self.assertEqual(found[0]["canonical"], "https://example.com/pricing")

    def test_a_trailing_slash_is_not_a_canonical_mismatch(self):
        rows = [{field: None for field in CANONICAL_FIELDS} for _ in range(1)]
        rows[0].update({"url": "https://e.com/page/", "canonical": "https://e.com/page", "status": 200})
        self.assertEqual(non_self_canonical(rows), [])

    def test_only_chained_redirects_are_reported(self):
        chains = redirect_chains(self.rows)
        self.assertEqual([c["url"] for c in chains], ["https://example.com/old"])
        self.assertEqual(chains[0]["then_status"], 301)

    def test_broken_urls_are_ordered_by_inlinks_so_severity_is_visible(self):
        found = broken(self.rows)
        self.assertEqual([r["url"] for r in found], ["https://example.com/gone"])
        self.assertEqual(found[0]["inlinks"], 14)

    def test_analyse_returns_every_section(self):
        result = analyse(self.rows)
        for key in (
            "summary", "broken", "redirect_chains", "duplicate_titles",
            "duplicate_descriptions", "duplicate_h1", "missing_titles",
            "missing_descriptions", "missing_h1", "non_self_canonical", "orphans", "thin",
        ):
            self.assertIn(key, result)


class TestProviderInterchangeability(unittest.TestCase):
    """Two exporters describing the same defect must produce the same finding."""

    def test_duplicate_titles_are_found_in_either_format(self):
        frog = duplicates(load_crawl(write(SCREAMING_FROG))["rows"], "title")
        bulb = duplicates(load_crawl(write(SITEBULB))["rows"], "title")
        self.assertEqual(len(frog), 1)
        self.assertEqual(len(bulb), 1)
        self.assertEqual(bulb[0]["value"], "Same Title")

    def test_a_hand_built_spreadsheet_works_if_the_headers_are_sensible(self):
        sheet = (
            "URL,Status Code,Page Title,Meta Description,Word Count,Internal Inlinks\n"
            "https://example.io/,200,Home,A description,700,50\n"
            "https://example.io/a,200,Dup,Another,100,0\n"
            "https://example.io/b,200,Dup,Another,100,4\n"
        )
        rows = load_crawl(write(sheet))["rows"]
        self.assertEqual(len(duplicates(rows, "title")), 1)
        self.assertEqual(orphans(rows), ["https://example.io/a"])
        self.assertEqual(len(thin(rows)), 2)

    def test_detect_exporter_never_blocks_a_load(self):
        # The label is for the report header only. An unknown exporter with good
        # headers must still load.
        self.assertEqual(detect_exporter(["url", "whatever"]), "unknown exporter")
        loaded = load_crawl(write("URL,Status Code\nhttps://e.com/,200\n"))
        self.assertEqual(loaded["exporter"], "unknown exporter")
        self.assertEqual(loaded["row_count"], 1)


if __name__ == "__main__":
    unittest.main()
