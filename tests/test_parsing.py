"""Extraction has to be exact. These are the assertions a prompt cannot make."""
import unittest

from seo_tools.parsing import count_words, parse_page

PAGE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
  <title>  Procurement   software
  for manufacturers </title>
  <meta name="description" content="One clear sentence about the product.">
  <meta name="robots" content="index, follow, max-snippet:-1">
  <meta name="viewport" content="width=device-width">
  <link rel="canonical" href="/pricing">
  <link rel="alternate" hreflang="de" href="https://example.com/de/pricing">
  <link rel="alternate" hreflang="x-default" href="https://example.com/pricing">
  <meta property="og:title" content="Pricing">
  <meta property="og:image" content="https://example.com/og.png">
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Product","name":"Widget",
   "offers":{"@type":"Offer","price":"10.00","priceCurrency":"EUR"}}
  </script>
  <style>.hidden { display: none } </style>
</head>
<body>
  <nav><a href="/">Home</a><a href="/about">About</a></nav>
  <main>
    <h1><span>Procurement</span><span>made simple</span></h1>
    <p>Real body copy that a reader would actually see.</p>
    <h2>Features</h2>
    <h4>Skipped a level here</h4>
    <img src="/a.png" alt="described">
    <img src="/b.png">
    <img src="/c.png" alt="">
    <a href="https://external.example/thing" rel="nofollow noopener">External</a>
    <a href="/internal">Internal</a>
    <a href="#anchor">Anchor</a>
    <a href="mailto:x@example.com">Mail</a>
  </main>
  <footer><a href="/legal">Legal</a></footer>
  <script>var ignored = "this text is not content";</script>
</body>
</html>"""


class TestBasics(unittest.TestCase):
    def setUp(self):
        self.page = parse_page(PAGE, "https://example.com/pricing")

    def test_title_whitespace_is_collapsed(self):
        self.assertEqual(self.page["title"], "Procurement software for manufacturers")

    def test_description_and_robots(self):
        self.assertEqual(self.page["meta_description"], "One clear sentence about the product.")
        self.assertIn("index", self.page["meta_robots_directives"])
        self.assertIn("max-snippet:-1", self.page["meta_robots_directives"])

    def test_relative_canonical_is_resolved_and_seen_as_self(self):
        self.assertEqual(self.page["canonical"], "https://example.com/pricing")
        self.assertIs(self.page["canonical_is_self"], True)

    def test_lang_and_hreflang(self):
        self.assertEqual(self.page["html_lang"], "en-GB")
        self.assertEqual({h["hreflang"] for h in self.page["hreflang"]}, {"de", "x-default"})

    def test_nested_span_headings_keep_word_boundaries(self):
        # The defect this caught on a real Webflow page: "Procurementmade simple".
        self.assertEqual(self.page["h1"], ["Procurement made simple"])

    def test_heading_levels_are_recorded_in_document_order(self):
        self.assertEqual([h["level"] for h in self.page["headings"]], [1, 2, 4])

    def test_open_graph_and_twitter_are_separated(self):
        self.assertEqual(
            self.page["open_graph"],
            {"og:title": "Pricing", "og:image": "https://example.com/og.png"},
        )
        self.assertEqual(self.page["twitter"], {"twitter:card": "summary_large_image"})

    def test_viewport_is_detected(self):
        self.assertTrue(self.page["has_viewport"])


class TestSchema(unittest.TestCase):
    def test_nested_types_are_all_found(self):
        page = parse_page(PAGE, "https://example.com/pricing")
        self.assertEqual(page["schema_types"], ["Offer", "Product"])

    def test_invalid_json_is_reported_not_swallowed(self):
        page = parse_page(
            '<script type="application/ld+json">{"@type": "Product",}</script>', "https://e.com/"
        )
        block = page["schema_blocks"][0]
        self.assertIs(block["valid_json"], False)
        self.assertIn("line", block["error"])

    def test_graph_form_is_walked(self):
        html = (
            '<script type="application/ld+json">'
            '{"@graph":[{"@type":"Organization","name":"A"},{"@type":["WebSite","Thing"]}]}'
            "</script>"
        )
        self.assertEqual(
            parse_page(html, "https://e.com/")["schema_types"],
            ["Organization", "Thing", "WebSite"],
        )


class TestCounting(unittest.TestCase):
    def setUp(self):
        self.page = parse_page(PAGE, "https://example.com/pricing")

    def test_script_and_style_text_is_not_content(self):
        self.assertNotIn("ignored", self.page["text_preview"])
        self.assertNotIn("display", self.page["text_preview"])

    def test_main_content_excludes_nav_and_footer(self):
        self.assertLess(self.page["main_word_count"], self.page["word_count"])

    def test_images_without_alt_counts_empty_alt_too(self):
        self.assertEqual(self.page["images"], 3)
        self.assertEqual(self.page["images_missing_alt"], 2)

    def test_internal_and_external_links_are_split(self):
        self.assertEqual(self.page["links_external"], 1)
        self.assertEqual(self.page["links_internal"], 4)  # home, about, internal, legal
        self.assertEqual(self.page["links_nofollow"], 1)

    def test_word_count_ignores_digits_and_punctuation(self):
        self.assertEqual(count_words("one two 3 4! five"), 3)


class TestEdgeCases(unittest.TestCase):
    def test_empty_input_does_not_crash(self):
        page = parse_page("", "https://e.com/")
        self.assertIs(page["ok"], True)
        self.assertIsNone(page["title"])
        self.assertEqual(page["word_count"], 0)

    def test_unclosed_tags_still_parse(self):
        page = parse_page("<html><body><h1>Open<p>Text", "https://e.com/")
        self.assertIs(page["ok"], True)
        self.assertEqual(page["h1"], ["Open Text"])

    def test_missing_description_is_none_and_empty_is_empty_string(self):
        self.assertIsNone(parse_page("<html></html>", "https://e.com/")["meta_description"])
        self.assertEqual(
            parse_page('<meta name="description" content="">', "https://e.com/")[
                "meta_description"
            ],
            "",
        )

    def test_client_rendered_shell_is_flagged(self):
        page = parse_page('<html><body><div id="root"></div></body></html>', "https://e.com/")
        self.assertIs(page["requires_js"], True)

    def test_a_full_page_with_an_app_root_is_not_flagged(self):
        html = '<html><body><div id="root"><p>{}</p></div></body></html>'.format("word " * 200)
        self.assertIs(parse_page(html, "https://e.com/")["requires_js"], False)

    def test_self_closing_tags_do_not_unbalance_the_depth_counters(self):
        page = parse_page(
            "<html><body><main><br/><p>Body copy here</p><img src='x.png'/></main></body></html>",
            "https://e.com/",
        )
        self.assertEqual(page["main_word_count"], 3)

    def test_parsing_is_deterministic(self):
        # Two runs over the same bytes must agree, or every baseline is noise.
        first = parse_page(PAGE, "https://example.com/pricing")
        second = parse_page(PAGE, "https://example.com/pricing")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
