"""Security regressions. Every case here was a live weakness before it was a test.

Found by probing rather than reading, which is why several are encodings a review
would pass over: a decimal-encoded loopback address, a hostname carrying a null
byte, a 200 KB response that expands to 200 MB.
"""
import gzip
import io
import unittest
import zlib
from contextlib import redirect_stderr, redirect_stdout

from seo_tools.cli import main
from seo_tools.fetching import MAX_DECOMPRESSED, _decompress
from seo_tools.safety import UrlNotAllowed, redact, validate_url

# Every notation for an address that must never be reached. A guard that checks
# for the string "127.0.0.1" passes none of these.
MUST_BLOCK = [
    "http://127.0.0.1/", "http://2130706433/", "http://0177.0.0.1/", "http://0x7f000001/",
    "http://127.1/", "http://0/", "http://[::1]/", "http://[::]/",
    "http://[::ffff:127.0.0.1]/", "http://[::ffff:7f00:1]/",
    "http://169.254.169.254/latest/meta-data/", "http://[fd00:ec2::254]/",
    "http://metadata.google.internal/", "http://100.100.100.200/",
    "http://10.1.2.3/", "http://172.20.1.1/", "http://192.168.0.1/", "http://169.254.1.1/",
    # Shared address space, RFC 6598. Reachable inside an ISP and not public.
    "http://100.64.0.1/", "http://100.127.255.254/",
    "http://224.0.0.1/", "http://240.0.0.1/", "http://255.255.255.255/",
    "http://localhost/", "http://localhost./", "http://LOCALHOST/",
    "http://printer.local/", "http://db.internal/", "http://router.home.arpa/",
    "file:///etc/passwd", "gopher://127.0.0.1:11211/", "dict://127.0.0.1:11211/",
    "ftp://example.com/", "data:text/html,<script>1</script>", "javascript:alert(1)",
    "http://user:pass@example.com/", "http://expected.com@127.0.0.1/",
    "//127.0.0.1/", "",
]


class TestSsrfGuard(unittest.TestCase):
    def test_every_private_and_encoded_form_is_refused(self):
        for url in MUST_BLOCK:
            with self.subTest(url=url):
                with self.assertRaises(UrlNotAllowed):
                    validate_url(url)

    def test_a_public_address_is_still_allowed(self):
        self.assertTrue(validate_url("http://93.184.216.34/"))
        self.assertTrue(validate_url("https://example.com/"))

    def test_ipv4_mapped_ipv6_is_judged_as_its_ipv4_form(self):
        # Python 3.13 taught is_private and is_loopback to look through the
        # mapping; 3.9 does not, so this was classified differently depending on
        # the interpreter. CI caught it on 3.9 only.
        from seo_tools.safety import _is_public_address

        for mapped, public in (
            ("::ffff:127.0.0.1", False),
            ("::ffff:7f00:1", False),
            ("::ffff:10.0.0.1", False),
            ("::ffff:169.254.169.254", False),
            ("::ffff:8.8.8.8", True),
        ):
            with self.subTest(address=mapped):
                self.assertIs(_is_public_address(mapped), public)

    def test_shared_address_space_is_not_public(self):
        # is_private is False for 100.64.0.0/10, so the explicit range list
        # missed it. is_global catches it.
        with self.assertRaises(UrlNotAllowed) as caught:
            validate_url("http://100.64.0.1/")
        self.assertIn("not a public address", str(caught.exception))


class TestControlCharacters(unittest.TestCase):
    """A hostname with a null byte is resolved as its prefix and written whole.

    getaddrinfo truncates at the null, so "example.com\\x00.evil" resolves to
    example.com and passes validation while naming a different host. That
    mismatch is the bug, whatever the HTTP client does afterwards.
    """

    def test_a_null_byte_is_refused(self):
        with self.assertRaises(UrlNotAllowed) as caught:
            validate_url("http://example.com" + chr(0) + ".evil.invalid/")
        self.assertIn("control character", str(caught.exception))

    def test_carriage_return_and_newline_are_refused(self):
        for char in (chr(13), chr(10), chr(9), chr(11), chr(127)):
            with self.subTest(char=repr(char)):
                with self.assertRaises(UrlNotAllowed):
                    validate_url("http://example.com/" + char + "x")

    def test_unicode_line_separators_are_refused(self):
        for char in (" ", " "):
            with self.subTest(char=repr(char)):
                with self.assertRaises(UrlNotAllowed):
                    validate_url("http://example.com/" + char)

    def test_an_ordinary_url_is_unaffected(self):
        self.assertTrue(validate_url("https://example.com/a/b?c=d&e=f#g"))


class TestDecompressionBombs(unittest.TestCase):
    """A capped download is not a cap on memory. Gzip exceeds 1000 to 1 easily."""

    def test_a_gzip_bomb_is_bounded(self):
        bomb = gzip.compress(b"A" * (200 * 1024 * 1024))
        self.assertLess(len(bomb), 1024 * 1024, "the bomb should be small compressed")
        out = _decompress(bomb, "gzip")
        self.assertLessEqual(len(out), MAX_DECOMPRESSED)

    def test_a_deflate_bomb_is_bounded(self):
        machine = zlib.compressobj()
        bomb = machine.compress(b"B" * (200 * 1024 * 1024)) + machine.flush()
        out = _decompress(bomb, "deflate")
        self.assertLessEqual(len(out), MAX_DECOMPRESSED)

    def test_ordinary_bodies_still_round_trip(self):
        self.assertEqual(_decompress(gzip.compress(b"hello world"), "gzip"), b"hello world")
        machine = zlib.compressobj()
        payload = machine.compress(b"hello deflate") + machine.flush()
        self.assertEqual(_decompress(payload, "deflate"), b"hello deflate")

    def test_a_mislabelled_encoding_returns_the_body_rather_than_raising(self):
        self.assertEqual(_decompress(b"not compressed", "gzip"), b"not compressed")
        self.assertEqual(_decompress(b"", "gzip"), b"")


class TestXmlHandling(unittest.TestCase):
    def test_an_external_entity_cannot_read_a_local_file(self):
        from seo_tools.sitemaps import parse_sitemap

        xxe = (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            b"<urlset><url><loc>&xxe;</loc></url></urlset>"
        )
        result = parse_sitemap(xxe, "https://example.com/sitemap.xml")
        self.assertIs(result["ok"], False)
        self.assertIn("entity", result["error"].lower())

    def test_a_gzipped_sitemap_is_bounded(self):
        from seo_tools.sitemaps import MAX_BYTES_UNCOMPRESSED, parse_sitemap

        bomb = gzip.compress(b"C" * (200 * 1024 * 1024))
        result = parse_sitemap(bomb, "https://example.com/sitemap.xml.gz")
        self.assertIs(result["ok"], False)
        self.assertLess(MAX_BYTES_UNCOMPRESSED, 200 * 1024 * 1024)


class TestCredentialsNeverReachOutput(unittest.TestCase):
    """A password in a URL must not land in stdout, a JSON payload or a log."""

    SECRET = "sup3rsecret"

    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                main(argv)
        except SystemExit:
            pass
        return out.getvalue() + err.getvalue()

    def test_redact_strips_userinfo_and_keeps_the_rest(self):
        self.assertEqual(
            redact("http://user:{}@example.com/pricing?a=1".format(self.SECRET)),
            "http://<redacted>@example.com/pricing?a=1",
        )

    def test_redact_leaves_a_clean_url_alone(self):
        self.assertEqual(redact("https://example.com/x"), "https://example.com/x")

    def test_no_command_echoes_the_password(self):
        url = "http://user:{}@example.com/".format(self.SECRET)
        for command in ("page", "fetch", "robots", "sitemap", "meta", "headings", "schema"):
            for extra in ([], ["--json"]):
                with self.subTest(command=command, json=bool(extra)):
                    output = self.run_cli([command, url] + extra)
                    self.assertNotIn(self.SECRET, output)


class TestKnownLimits(unittest.TestCase):
    """Written down so the guard is not mistaken for something stronger.

    validate_url resolves a hostname and checks every address, then urllib
    resolves it again when it connects. A DNS answer that changes between those
    two moments, deliberately, is not caught: closing that needs pinning the
    address and connecting to it directly, which urllib will not do without a
    custom opener. Documented in docs/security.md rather than implied away.
    """

    def test_the_guard_checks_every_address_a_name_resolves_to(self):
        # The mitigation that is in place: one public address is not enough if
        # another is private.
        from seo_tools import safety

        original = safety.resolve_host
        safety.resolve_host = lambda host: ["93.184.216.34", "10.0.0.1"]
        try:
            with self.assertRaises(UrlNotAllowed) as caught:
                validate_url("http://multi.example/")
            self.assertIn("10.0.0.1", str(caught.exception))
        finally:
            safety.resolve_host = original


class TestNumericHostsAreRefusedByRule(unittest.TestCase):
    """These were blocked on Windows only because the resolver happened to fail.

    CI on macOS accepted `0177.0.0.1`, because getaddrinfo there parses octal and
    short forms that Windows rejects. A guard that depends on which resolver it
    runs against is not a guard, so an IP-shaped host now has to parse as a valid
    address or be refused outright.
    """

    AMBIGUOUS = [
        "http://0177.0.0.1/", "http://2130706433/", "http://0x7f000001/",
        "http://127.1/", "http://0/", "http://1.2.3.4.5/",
        "http://010.010.010.010/", "http://0177.1/", "http://999.999.999.999/",
    ]

    def test_refused_for_the_stated_reason_and_not_by_dns_failure(self):
        for url in self.AMBIGUOUS:
            with self.subTest(url=url):
                with self.assertRaises(UrlNotAllowed) as caught:
                    validate_url(url)
                self.assertIn(
                    "looks like a numeric address",
                    str(caught.exception),
                    "{} was refused, but by DNS failure rather than by rule, so it "
                    "would be allowed on a platform whose resolver parses it".format(url),
                )

    def test_real_hostnames_and_valid_addresses_are_unaffected(self):
        for url in (
            "https://example.com/", "http://93.184.216.34/", "http://8.8.8.8/",
            "https://cafe.ba/", "https://ab.cd/", "http://[::ffff:1.2.3.4]/",
        ):
            with self.subTest(url=url):
                self.assertTrue(validate_url(url))


if __name__ == "__main__":
    unittest.main()
