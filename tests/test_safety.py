"""The URL guard. If these pass by accident the whole package is unsafe.

unittest rather than pytest so the suite runs with nothing installed:
    python -m unittest discover -s tests
pytest will also collect these if you happen to have it.
"""
import unittest

from seo_tools.safety import UrlNotAllowed, normalise_url, validate_url

MUST_REFUSE = [
    "file:///etc/passwd",
    "ftp://example.com/x",
    "javascript:alert(1)",
    "gopher://example.com",
    "",
    "   ",
    "https://",
    "http://user:pass@example.com/",
    "http://127.0.0.1/admin",
    "http://localhost/admin",
    "http://localhost./",
    "http://[::1]/admin",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.1/",
    "http://192.168.1.1/",
    "http://172.16.0.1/",
    "http://0.0.0.0/",
    "http://metadata.google.internal/",
    "http://printer.local/",
    "http://db.internal/",
]


class TestValidate(unittest.TestCase):
    def test_refuses_what_it_must(self):
        for url in MUST_REFUSE:
            with self.subTest(url=url):
                with self.assertRaises(UrlNotAllowed):
                    validate_url(url)

    def test_allows_a_public_ip_literal(self):
        self.assertEqual(validate_url("http://93.184.216.34/"), "http://93.184.216.34/")

    def test_allow_private_is_opt_in_only(self):
        self.assertTrue(validate_url("http://127.0.0.1:8000/x", allow_private=True))
        with self.assertRaises(UrlNotAllowed):
            validate_url("http://127.0.0.1:8000/x")

    def test_allow_private_relaxes_only_the_address_range_check(self):
        # fetch() carries this flag to every redirect hop, so anything a
        # fixture server could redirect into has to stay blocked regardless.
        still_blocked = [
            "http://169.254.169.254/latest/meta-data/",
            "http://metadata.google.internal/",
            "http://100.100.100.200/",
            "file:///etc/passwd",
            "http://user:pass@127.0.0.1/",
            "http://printer.local/",
        ]
        for url in still_blocked:
            with self.subTest(url=url):
                with self.assertRaises(UrlNotAllowed):
                    validate_url(url, allow_private=True)

    def test_the_message_names_the_rule_that_tripped(self):
        with self.assertRaises(UrlNotAllowed) as caught:
            validate_url("http://10.0.0.1/")
        self.assertIn("not a public address", str(caught.exception))


class TestNormalise(unittest.TestCase):
    def test_lowercases_scheme_and_host_but_not_path(self):
        self.assertEqual(normalise_url("HTTPS://Example.COM/Path"), "https://example.com/Path")

    def test_drops_default_ports_keeps_others(self):
        self.assertEqual(normalise_url("https://example.com:443/a"), "https://example.com/a")
        self.assertEqual(normalise_url("http://example.com:80/a"), "http://example.com/a")
        self.assertEqual(normalise_url("https://example.com:8443/a"), "https://example.com:8443/a")

    def test_strips_tracking_and_sorts_the_rest(self):
        self.assertEqual(
            normalise_url("https://example.com/p?b=2&utm_source=news&a=1&gclid=xyz"),
            "https://example.com/p?a=1&b=2",
        )

    def test_drops_fragment_and_trailing_slash(self):
        self.assertEqual(normalise_url("https://example.com/p/#section"), "https://example.com/p")

    def test_root_keeps_its_slash(self):
        self.assertEqual(normalise_url("https://example.com/"), "https://example.com/")

    def test_the_same_page_twice_gets_one_key(self):
        self.assertEqual(
            normalise_url("https://Example.com/pricing/?utm_campaign=q3#top"),
            normalise_url("https://example.com:443/pricing"),
        )

    def test_a_real_parameter_is_not_mistaken_for_tracking(self):
        self.assertEqual(
            normalise_url("https://example.com/search?page=2"), "https://example.com/search?page=2"
        )


if __name__ == "__main__":
    unittest.main()
