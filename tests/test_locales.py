"""Locale behaviour. The pack is for anyone, so nothing here may assume English.

Every test in this file corresponds to a bug that was live before it was written.
The pattern was the same each time: code that looked general because it handled
English and German, and silently produced a wrong number or no number at all for
everything else.
"""
import json
import pathlib
import tempfile
import unittest

from seo_tools.gsc import GscError, load_csv, parse_column_override
from seo_tools.audits import check_meta
from seo_tools.parsing import count_words, counting_basis, parse_page
from seo_tools.robots import AI_AGENTS, RobotsTxt
from seo_tools.typography import char_units, measure_px, measure_title, truncate_to_px

# Real Search Console UI export headers. Anything that fails here is a locale
# whose users cannot analyse their own traffic.
GSC_HEADERS = {
    "English": "Top queries,Clicks,Impressions,CTR,Position",
    "German": "Häufigste Suchanfragen;Klicks;Impressionen;Klickrate;Durchschnittliche Position",
    "French": "Requêtes les plus fréquentes,Clics,Impressions,CTR,Position moyenne",
    "Spanish": "Consultas principales,Clics,Impresiones,CTR,Posición media",
    "Italian": "Query principali,Clic,Impressioni,CTR,Posizione media",
    "Dutch": "Populairste zoekopdrachten,Klikken,Vertoningen,CTR,Positie",
    "Polish": "Najpopularniejsze zapytania,Kliknięcia,Wyświetlenia,CTR,Pozycja",
    "Turkish": "En popüler sorgular,Tıklama,Görüntüleme,CTR,Ortalama konum",
    "Czech": "Nejčastější dotazy,Kliknutí,Zobrazení,CTR,Průměrná pozice",
    "Swedish": "Vanligaste sökfrågorna,Klick,Visningar,Klickfrekvens,Genomsnittlig position",
    "Japanese": "上位のクエリ,クリック数,表示回数,CTR,掲載順位",
    "Korean": "인기 검색어,클릭수,노출수,클릭률,평균 게재순위",
    "Chinese": "热门查询,点击次数,展示次数,点击率,平均排名",
    "Russian": "Поисковый запрос,Клики,Показы,CTR,Позиция",
}
REQUIRED = {"query", "clicks", "impressions", "ctr", "position"}


def write_csv(header, row="foo,10,100,10%,4.2"):
    delimiter = ";" if ";" in header else ","
    if delimiter == ";":
        row = row.replace(",", ";")
    path = pathlib.Path(tempfile.mkdtemp()) / "export.csv"
    path.write_text(header + "\n" + row + "\n", encoding="utf-8")
    return str(path)


class TestSearchConsoleLocales(unittest.TestCase):
    def test_every_supported_locale_resolves_all_five_columns(self):
        for name, header in GSC_HEADERS.items():
            with self.subTest(locale=name):
                loaded = load_csv(write_csv(header))
                missing = REQUIRED - set(loaded["columns_detected"])
                self.assertEqual(missing, set(), "{} lost {}".format(name, sorted(missing)))

    def test_values_parse_and_not_just_headers(self):
        for name, header in GSC_HEADERS.items():
            with self.subTest(locale=name):
                row = load_csv(write_csv(header))["rows"][0]
                self.assertEqual(row["clicks"], 10.0)
                self.assertEqual(row["impressions"], 100.0)
                self.assertEqual(row["position"], 4.2)

    def test_a_cjk_header_is_not_stripped_to_nothing(self):
        # The original punctuation class was [^a-z0-9 ], which deleted every
        # non-ASCII character, so these headers reduced to an empty string.
        for locale in ("Japanese", "Korean", "Chinese", "Russian"):
            with self.subTest(locale=locale):
                loaded = load_csv(write_csv(GSC_HEADERS[locale]))
                self.assertIn("query", loaded["columns_detected"])

    def test_an_unknown_locale_gets_a_usable_error(self):
        with self.assertRaises(GscError) as caught:
            load_csv(write_csv("Alpha,Beta,Gamma,Delta,Epsilon"))
        self.assertIn("--columns", str(caught.exception))


class TestColumnOverride(unittest.TestCase):
    def test_it_resolves_a_header_in_no_known_language(self):
        loaded = load_csv(
            write_csv("Aa,Bb,Cc,Dd,Ee"), columns="query,clicks,impressions,ctr,position"
        )
        self.assertEqual(REQUIRED, set(loaded["columns_detected"]))
        self.assertEqual(loaded["columns_resolved_by"], "the --columns override")
        self.assertEqual(loaded["rows"][0]["position"], 4.2)

    def test_a_dash_skips_a_column(self):
        mapping = parse_column_override("query,-,impressions", 3)
        self.assertEqual(mapping, {0: "query", 2: "impressions"})

    def test_an_invalid_name_is_refused_with_the_valid_list(self):
        with self.assertRaises(GscError) as caught:
            parse_column_override("query,sessions", 2)
        self.assertIn("sessions", str(caught.exception))
        self.assertIn("impressions", str(caught.exception))

    def test_naming_more_columns_than_the_file_has_is_refused(self):
        with self.assertRaises(GscError):
            parse_column_override("query,clicks,impressions", 2)

    def test_an_empty_spec_is_refused(self):
        with self.assertRaises(GscError):
            parse_column_override(",,", 3)


class TestWordCounting(unittest.TestCase):
    def test_scripts_without_word_spaces_are_not_counted_as_one_word(self):
        # Before the fix these all returned 1, which made every CJK page look
        # empty and tripped the client-rendering heuristic on all of them.
        self.assertEqual(count_words("これは調達ソフトウェアのテストです"), 17)
        self.assertEqual(count_words("采购软件适用于制造业企业"), 12)

    def test_korean_uses_spaces_so_it_is_counted_by_words(self):
        self.assertEqual(count_words("조달 소프트웨어"), 2)

    def test_space_separated_scripts_are_unchanged(self):
        self.assertEqual(count_words("Procurement software for manufacturers"), 4)
        self.assertEqual(count_words("Закупочное программное обеспечение"), 3)

    def test_mixed_script_text_counts_both_halves(self):
        # Two Latin words, plus 10 kanji and kana counted individually. The two
        # passes are additive and must not double count or drop either side.
        self.assertEqual(count_words("Mercanis 調達プラットフォーム platform"), 12)
        self.assertEqual(count_words("調達プラットフォーム"), 10)
        self.assertEqual(count_words("Mercanis platform"), 2)

    def test_the_basis_is_reported_so_a_caller_can_caveat_the_number(self):
        self.assertEqual(counting_basis("plain english words"), "words")
        self.assertIn("Japanese", counting_basis("調達ソフトウェア"))
        self.assertIn("unreliable", counting_basis("ซอฟต์แวร์จัดซื้อ"))

    def test_a_cjk_page_is_not_flagged_as_client_rendered(self):
        # The heuristic is "app root element plus almost no text". A CJK page
        # with real content used to satisfy it because the count was 1.
        html = "<html><body><div id='root'><p>{}</p></div></body></html>".format("採購軟體適用於製造業" * 20)
        page = parse_page(html, "https://example.com/")
        self.assertGreater(page["main_word_count"], 100)
        self.assertIs(page["requires_js"], False)


class TestPixelWidthAcrossScripts(unittest.TestCase):
    def test_a_wide_character_is_not_measured_as_a_latin_one(self):
        # Ten CJK characters render roughly twice as wide as ten Latin ones.
        latin = measure_px("aaaaaaaaaa", 20)
        cjk = measure_px("采购软件适用于制造业", 20)
        self.assertGreater(cjk, latin * 1.5)

    def test_a_combining_mark_adds_no_width(self):
        self.assertEqual(measure_px("e", 20), measure_px("é", 20))
        self.assertEqual(char_units("́"), 0)

    def test_a_long_cjk_title_is_correctly_reported_as_truncating(self):
        # Measured as Latin, this fitted inside the budget. It does not.
        measured = measure_title("調達プラットフォーム" * 4)
        self.assertTrue(measured["truncates"])

    def test_the_preview_is_useful_for_text_with_no_spaces(self):
        # Word-boundary cutting alone returned a bare ellipsis here.
        preview = truncate_to_px("采购软件适用于制造业企业" * 6, 580, 20)
        self.assertTrue(preview.endswith("…"))
        self.assertGreater(len(preview), 5)
        self.assertLessEqual(measure_px(preview, 20), 580)

    def test_the_method_label_says_which_estimate_was_used(self):
        self.assertIn("Arial", measure_title("Latin title")["method"])
        self.assertIn("fullwidth", measure_title("調達プラットフォーム")["method"])


class TestPassFailIsScriptNeutral(unittest.TestCase):
    """Every threshold decision must be in pixels, never in characters.

    A character floor called a 28-character Japanese title too short while it
    filled 85% of the available width.
    """

    def test_a_full_width_cjk_title_is_not_called_short(self):
        page = {
            "title": "調達プラットフォーム | 製造業向けAI購買ソフトウェア",
            "meta_description": "調達業務を自動化し、サプライヤー管理と契約管理を一つのプラットフォームで実現します。導入事例をご覧ください。",
            "h1": [],
        }
        checks = {f["check"] for f in check_meta(page)}
        self.assertNotIn("title.short", checks)
        self.assertNotIn("description.short", checks)

    def test_a_genuinely_short_latin_title_is_still_called_short(self):
        checks = {f["check"] for f in check_meta({"title": "Pricing", "meta_description": "x" * 200, "h1": []})}
        self.assertIn("title.short", checks)

    def test_a_short_cjk_title_is_still_caught(self):
        # Three wide characters is genuinely short in any script.
        checks = {f["check"] for f in check_meta({"title": "調達費", "meta_description": "x" * 200, "h1": []})}
        self.assertIn("title.short", checks)

    def test_the_finding_carries_the_method_for_its_script(self):
        findings = check_meta({"title": "調達費", "meta_description": "x" * 200, "h1": []})
        short = [f for f in findings if f["check"] == "title.short"][0]
        self.assertIn("fullwidth", short["method"])


class TestRegionalCrawlers(unittest.TestCase):
    def test_market_leading_engines_outside_the_west_are_covered(self):
        for agent in ("YandexBot", "Baiduspider", "Yeti", "SeznamBot", "PetalBot"):
            with self.subTest(agent=agent):
                self.assertIn(agent, AI_AGENTS)

    def test_blocking_a_regional_engine_is_reported_with_its_market(self):
        robots = RobotsTxt("User-agent: Baiduspider\nDisallow: /\n", 200)
        audit = robots.audit_ai_agents("https://example.com/")
        blocked = {row["agent"]: row for row in audit["agents"] if not row["allowed"]}
        self.assertIn("Baiduspider", blocked)
        self.assertIn("China", blocked["Baiduspider"]["cost_of_blocking"])

    def test_applebot_is_distinguished_from_applebot_extended(self):
        # One governs search visibility, the other only training. Blocking the
        # wrong one is the same class of mistake as the Google-Extended trap.
        self.assertIn("search index", AI_AGENTS["Applebot"]["purpose"])
        self.assertEqual(AI_AGENTS["Applebot-Extended"]["purpose"], "training")

    def test_a_regional_engine_is_matched_by_its_own_group(self):
        robots = RobotsTxt("User-agent: *\nDisallow: /\n\nUser-agent: Yeti\nAllow: /\n", 200)
        self.assertTrue(robots.can_fetch("Yeti", "https://example.com/page")["allowed"])
        self.assertFalse(robots.can_fetch("SomeOtherBot", "https://example.com/page")["allowed"])


class TestExtractedWidths(unittest.TestCase):
    """Cyrillic, Greek and Hebrew come from the font, not from a default.

    Before this, every glyph in those scripts fell through to DEFAULT_WIDTH of
    556. Cyrillic Sha is 917, so a Russian title was under-measured by up to 65%
    per wide character.
    """

    def test_cyrillic_is_not_measured_at_the_default(self):
        from seo_tools.typography import DEFAULT_WIDTH, char_units

        self.assertEqual(char_units("Ш"), 917)
        self.assertEqual(char_units("ж"), 669)
        self.assertNotEqual(char_units("Ш"), DEFAULT_WIDTH)

    def test_greek_and_hebrew_are_tabulated(self):
        from seo_tools.typography import EXTRA_WIDTHS

        self.assertIn("ω", EXTRA_WIDTHS)
        self.assertIn("א", EXTRA_WIDTHS)

    def test_the_sharp_s_error_the_font_caught(self):
        # The hand-written table said 556. The font says 611. This matters for
        # every German title containing one.
        from seo_tools.typography import char_units

        self.assertEqual(char_units("ß"), 611)

    def test_a_wide_cyrillic_title_is_measured_wider_than_a_narrow_one(self):
        from seo_tools.typography import measure_px

        self.assertGreater(measure_px("ШШШШ", 20), measure_px("iiii", 20) * 3)

    def test_cyrillic_text_gets_its_own_method_label(self):
        from seo_tools.typography import measure_title

        method = measure_title("Закупочное программное обеспечение")["method"]
        self.assertIn("extracted from the font", method)
        self.assertNotIn("UNRELIABLE", method)


class TestUnmeasurableScripts(unittest.TestCase):
    """Scripts where summing per-character widths is the wrong measurement.

    Arabic is cursive, so letters join and change form. The Indic scripts form
    conjuncts and reorder vowel signs, and Arial has no Devanagari at all. A
    number for either is not a rough estimate, it is wrong, so the pack says so
    rather than producing a verdict.
    """

    def test_arabic_and_devanagari_are_flagged(self):
        from seo_tools.typography import unmeasurable_scripts

        self.assertEqual(
            [b["script"] for b in unmeasurable_scripts("برمجيات المشتريات")], ["Arabic"]
        )
        self.assertEqual(
            [b["script"] for b in unmeasurable_scripts("खरीद सॉफ्टवेयर")], ["Devanagari"]
        )

    def test_latin_cyrillic_and_cjk_are_not_flagged(self):
        from seo_tools.typography import unmeasurable_scripts

        for text in ("Procurement software", "Закупочное ПО", "調達ソフトウェア", "조달 소프트웨어"):
            with self.subTest(text=text):
                self.assertEqual(unmeasurable_scripts(text), [])

    def test_the_method_says_unreliable_and_gives_the_reason(self):
        from seo_tools.typography import measure_title

        method = measure_title("برمجيات المشتريات")["method"]
        self.assertIn("UNRELIABLE", method)
        self.assertIn("cursive", method)

    def test_no_truncation_verdict_is_issued_on_an_unreliable_width(self):
        # A pass or fail on a number that does not mean what it looks like is
        # worse than no verdict.
        long_arabic = "برمجيات المشتريات للمؤسسات " * 6
        checks = {f["check"] for f in check_meta({"title": long_arabic, "meta_description": "x" * 200, "h1": []})}
        self.assertIn("title.width_unmeasurable", checks)
        self.assertNotIn("title.too_wide", checks)
        self.assertNotIn("title.short", checks)

    def test_a_measurable_script_still_gets_a_verdict(self):
        checks = {f["check"] for f in check_meta({"title": "Ш" * 40, "meta_description": "x" * 200, "h1": []})}
        self.assertIn("title.too_wide", checks)
        self.assertNotIn("title.width_unmeasurable", checks)


class TestNormaliseCommand(unittest.TestCase):
    """The join key, exposed as a command.

    A live agent was told to get this via `python -c "from seo_tools.safety
    import normalise_url; ..."`, which fails everywhere except the pack root.
    That is the defect the launcher exists to fix, reintroduced in a snippet, so
    it became a command instead.
    """

    def run_cli(self, argv):
        import io
        from contextlib import redirect_stderr, redirect_stdout

        from seo_tools.cli import main

        out, err = io.StringIO(), io.StringIO()
        code = 0
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = main(argv)
        except SystemExit as exc:
            code = int(exc.code or 0)
        return code, out.getvalue(), err.getvalue()

    def test_variants_of_one_url_collapse_to_one_key(self):
        code, out, _ = self.run_cli([
            "normalise",
            "https://Example.com/Pricing/?utm_source=news",
            "https://example.com:443/Pricing",
            "--json",
        ])
        self.assertEqual(code, 0)
        keys = {row["normalised"] for row in json.loads(out)["urls"]}
        self.assertEqual(len(keys), 1, "two spellings of one URL produced two keys")

    def test_a_non_url_is_flagged_rather_than_returned_as_a_key(self):
        code, out, _ = self.run_cli(["normalise", "notaurl", "--json"])
        self.assertEqual(code, 1)
        row = json.loads(out)["urls"][0]
        self.assertIs(row["ok"], False)
        self.assertIn("not a URL", row["error"])

    def test_a_good_url_exits_zero(self):
        code, _, _ = self.run_cli(["normalise", "https://example.com/a/"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
