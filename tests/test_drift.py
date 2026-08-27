"""Drift rules and the SQLite store, which together give the pack a memory."""
import tempfile
import unittest
from pathlib import Path

from seo_tools.drift import compare
from seo_tools.parsing import parse_page
from seo_tools.store import Store

BEFORE_HTML = """<html lang="en"><head>
<title>Pricing</title><meta name="description" content="What it costs.">
<link rel="canonical" href="https://example.com/pricing">
<script type="application/ld+json">{"@type":"Product","name":"Widget"}</script>
<meta property="og:title" content="Pricing">
</head><body><main><h1>Pricing</h1><h2>Plans</h2>
<p>%s</p><a href="/a">a</a><a href="/b">b</a><a href="/c">c</a><a href="/d">d</a>
</main></body></html>""" % ("word " * 300)


def snapshot(html, status=200, url="https://example.com/pricing"):
    page = parse_page(html, url)
    page["status"] = status
    return page


def baseline_from(html, **kwargs):
    page = snapshot(html, **kwargs)
    with tempfile.TemporaryDirectory() as home:
        with Store(Path(home)) as store:
            saved = store.save_baseline("https://example.com/pricing", page, html)
            return store.baseline_by_id(saved["baseline_id"])


def rules_fired(result):
    return {change["rule"] for change in result["changes"]}


class TestNoChange(unittest.TestCase):
    def test_the_same_page_twice_reports_nothing(self):
        result = compare(baseline_from(BEFORE_HTML), snapshot(BEFORE_HTML))
        self.assertEqual(result["changes"], [])
        self.assertEqual(result["verdict"], "no change against the baseline")


class TestCriticalChanges(unittest.TestCase):
    def setUp(self):
        self.baseline = baseline_from(BEFORE_HTML)

    def test_noindex_appearing_is_critical(self):
        after = BEFORE_HTML.replace("<head>", '<head><meta name="robots" content="noindex">')
        result = compare(self.baseline, snapshot(after))
        self.assertIn("robots.noindex_added", rules_fired(result))
        self.assertEqual(result["counts"]["critical"], 1)

    def test_a_removed_canonical_is_critical(self):
        after = BEFORE_HTML.replace('<link rel="canonical" href="https://example.com/pricing">', "")
        self.assertIn("canonical.removed", rules_fired(compare(self.baseline, snapshot(after))))

    def test_a_moved_canonical_is_critical(self):
        after = BEFORE_HTML.replace("/pricing\">", "/plans\">")
        self.assertIn("canonical.changed", rules_fired(compare(self.baseline, snapshot(after))))

    def test_a_cosmetically_different_canonical_is_not_a_change(self):
        # Caught on a live page: the baseline held a trailing slash and the page
        # did not, which raised a critical on two spellings of the same URL. A
        # false critical here is what gets a whole drift report ignored.
        for variant in (
            "https://example.com/pricing/",
            "https://example.com/pricing?utm_source=newsletter",
            "https://Example.com/pricing",
            "https://example.com:443/pricing",
        ):
            with self.subTest(variant=variant):
                after = BEFORE_HTML.replace(
                    'href="https://example.com/pricing"', 'href="{}"'.format(variant)
                )
                fired = rules_fired(compare(self.baseline, snapshot(after)))
                self.assertNotIn("canonical.changed", fired)

    def test_a_genuinely_different_path_still_fires(self):
        after = BEFORE_HTML.replace(
            'href="https://example.com/pricing"', 'href="https://example.com/pricing-old"'
        )
        self.assertIn("canonical.changed", rules_fired(compare(self.baseline, snapshot(after))))

    def test_losing_schema_types_is_critical(self):
        after = BEFORE_HTML.replace('{"@type":"Product","name":"Widget"}', "{}")
        result = compare(self.baseline, snapshot(after))
        self.assertIn("schema.types_removed", rules_fired(result))

    def test_a_page_that_starts_500ing_is_critical(self):
        result = compare(self.baseline, snapshot(BEFORE_HTML, status=500))
        change = [c for c in result["changes"] if c["rule"] == "status.changed"][0]
        self.assertEqual(change["severity"], "critical")

    def test_a_redirect_is_a_warning_not_critical(self):
        result = compare(self.baseline, snapshot(BEFORE_HTML, status=301))
        change = [c for c in result["changes"] if c["rule"] == "status.changed"][0]
        self.assertEqual(change["severity"], "warning")

    def test_content_moving_client_side_is_critical(self):
        after = '<html><head><title>Pricing</title></head><body><div id="root"></div></body></html>'
        result = compare(self.baseline, snapshot(after))
        self.assertIn("rendering.became_client_side", rules_fired(result))

    def test_a_lost_h1_is_critical_but_a_rewritten_one_is_a_warning(self):
        removed = compare(self.baseline, snapshot(BEFORE_HTML.replace("<h1>Pricing</h1>", "")))
        rewritten = compare(self.baseline, snapshot(BEFORE_HTML.replace("<h1>Pricing</h1>", "<h1>Plans</h1>")))
        self.assertEqual(
            [c["severity"] for c in removed["changes"] if c["rule"] == "h1.changed"], ["critical"]
        )
        self.assertEqual(
            [c["severity"] for c in rewritten["changes"] if c["rule"] == "h1.changed"], ["warning"]
        )


class TestTolerances(unittest.TestCase):
    def setUp(self):
        self.baseline = baseline_from(BEFORE_HTML)

    def test_small_copy_edits_are_below_the_noise_floor(self):
        after = BEFORE_HTML.replace("word " * 300, "word " * 310)  # about 3 percent
        self.assertNotIn("content.volume_changed", rules_fired(compare(self.baseline, snapshot(after))))

    def test_a_big_content_cut_is_flagged_as_a_warning(self):
        after = BEFORE_HTML.replace("word " * 300, "word " * 100)
        result = compare(self.baseline, snapshot(after))
        change = [c for c in result["changes"] if c["rule"] == "content.volume_changed"][0]
        self.assertEqual(change["severity"], "warning")

    def test_internal_links_halving_is_flagged(self):
        after = BEFORE_HTML.replace('<a href="/b">b</a><a href="/c">c</a><a href="/d">d</a>', "")
        self.assertIn("links.internal_halved", rules_fired(compare(self.baseline, snapshot(after))))


class TestVerdict(unittest.TestCase):
    def test_critical_dominates_the_verdict(self):
        after = BEFORE_HTML.replace("<head>", '<head><meta name="robots" content="noindex">').replace(
            "<h2>Plans</h2>", "<h2>Packages</h2>"
        )
        self.assertTrue(compare(baseline_from(BEFORE_HTML), snapshot(after))["verdict"].startswith("regression"))

    def test_info_only_reads_as_changed_not_broken(self):
        after = BEFORE_HTML.replace("<h2>Plans</h2>", "<h2>Packages</h2>")
        self.assertEqual(
            compare(baseline_from(BEFORE_HTML), snapshot(after))["verdict"], "changed, nothing critical"
        )


class TestStore(unittest.TestCase):
    def test_a_baseline_round_trips(self):
        with tempfile.TemporaryDirectory() as home:
            with Store(Path(home)) as store:
                page = snapshot(BEFORE_HTML)
                saved = store.save_baseline("https://example.com/pricing", page, BEFORE_HTML, label="v1")
                loaded = store.latest_baseline("https://example.com/pricing")
                self.assertEqual(loaded["baseline_id"], saved["baseline_id"])
                self.assertEqual(loaded["label"], "v1")
                self.assertEqual(loaded["snapshot"]["title"], "Pricing")

    def test_url_variants_resolve_to_the_same_baseline(self):
        with tempfile.TemporaryDirectory() as home:
            with Store(Path(home)) as store:
                store.save_baseline("https://example.com/pricing", snapshot(BEFORE_HTML), BEFORE_HTML)
                found = store.latest_baseline("https://Example.com/pricing/?utm_source=x")
                self.assertIsNotNone(found)

    def test_history_returns_newest_first(self):
        with tempfile.TemporaryDirectory() as home:
            with Store(Path(home)) as store:
                for label in ("first", "second", "third"):
                    store.save_baseline(
                        "https://example.com/pricing", snapshot(BEFORE_HTML), BEFORE_HTML, label=label
                    )
                history = store.history("https://example.com/pricing")
                self.assertEqual(len(history["baselines"]), 3)
                self.assertEqual(history["baselines"][0]["label"], "third")

    def test_an_unknown_url_returns_none_rather_than_raising(self):
        with tempfile.TemporaryDirectory() as home:
            with Store(Path(home)) as store:
                self.assertIsNone(store.latest_baseline("https://example.com/never-seen"))

    def test_the_database_is_created_on_first_use(self):
        with tempfile.TemporaryDirectory() as home:
            target = Path(home) / "nested" / "deeper"
            with Store(target) as store:
                self.assertTrue(store.path.exists())


if __name__ == "__main__":
    unittest.main()
