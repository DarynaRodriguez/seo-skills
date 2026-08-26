"""The network path, against a real local server rather than a mock.

A mocked socket would not have caught the things that actually break here:
redirect chains, a redirect pointing somewhere it should not, gzip bodies, and
pages that lie about their encoding. The server binds to 127.0.0.1 on a port
the OS picks, so nothing leaves the machine and nothing collides in CI.

Because the guard in safety.py blocks loopback by design, these tests pass
allow_private=True. Nothing in seo_tools/cli.py does.
"""
import gzip
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from seo_tools.fetching import decode_body, fetch, public_summary
from seo_tools.safety import UrlNotAllowed

HTML = (
    "<html lang='en'><head><title>Fixture</title>"
    "<meta name='description' content='A fixture page.'></head>"
    "<body><main><h1>Fixture</h1><p>Some body copy.</p></main></body></html>"
)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass  # keep the test output clean

    def _send(self, status, body=b"", headers=None):
        self.send_response(status)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        path = self.path
        if path == "/":
            self._send(200, HTML.encode("utf-8"), {"Content-Type": "text/html; charset=utf-8"})
        elif path == "/gzip":
            self._send(
                200,
                gzip.compress(HTML.encode("utf-8")),
                {"Content-Type": "text/html; charset=utf-8", "Content-Encoding": "gzip"},
            )
        elif path == "/latin1":
            # Declares utf-8 but sends latin-1. A real and common defect.
            self._send(
                200,
                "<html><head><title>café</title></head><body>x</body></html>".encode("latin-1"),
                {"Content-Type": "text/html; charset=utf-8"},
            )
        elif path == "/hop1":
            self._send(301, b"", {"Location": "/hop2"})
        elif path == "/hop2":
            self._send(302, b"", {"Location": "/"})
        elif path == "/loop":
            self._send(301, b"", {"Location": "/loop"})
        elif path == "/offsite":
            self._send(301, b"", {"Location": "http://169.254.169.254/latest/meta-data/"})
        elif path == "/noindex":
            self._send(
                200,
                HTML.encode("utf-8"),
                {"Content-Type": "text/html; charset=utf-8", "X-Robots-Tag": "noindex"},
            )
        elif path == "/gone":
            self._send(404, b"<html><body>Not here</body></html>", {"Content-Type": "text/html"})
        elif path == "/teapot":
            self._send(418, b"short and stout", {"Content-Type": "text/plain"})
        else:
            self._send(404, b"")


class ServerCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = "http://127.0.0.1:{}".format(cls.server.server_address[1])
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def get(self, path, **kwargs):
        kwargs.setdefault("allow_private", True)
        kwargs.setdefault("timeout", 10)
        return fetch(self.base + path, **kwargs)


class TestHappyPath(ServerCase):
    def test_a_plain_page(self):
        result = self.get("/")
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["redirect_count"], 0)
        self.assertIn("Fixture", result["text"])
        self.assertEqual(result["encoding"], "utf-8")
        self.assertEqual(result["encoding_source"], "content-type header")

    def test_gzip_is_decompressed(self):
        result = self.get("/gzip")
        self.assertTrue(result["ok"])
        self.assertIn("Fixture", result["text"])

    def test_seo_headers_survive_into_the_summary(self):
        summary = public_summary(self.get("/noindex"))
        self.assertEqual(summary["headers"]["x-robots-tag"], "noindex")

    def test_the_summary_carries_no_raw_bytes(self):
        summary = public_summary(self.get("/"))
        self.assertNotIn("body", summary)
        self.assertNotIn("text", summary)


class TestRedirects(ServerCase):
    def test_the_whole_chain_is_reported_not_just_the_destination(self):
        result = self.get("/hop1")
        self.assertTrue(result["ok"])
        self.assertEqual(result["redirect_count"], 2)
        statuses = [hop["status"] for hop in result["redirect_chain"]]
        self.assertEqual(statuses, [301, 302, 200])
        self.assertTrue(result["final_url"].endswith("/"))

    def test_a_redirect_loop_ends_with_an_error_not_a_hang(self):
        result = self.get("/loop", max_redirects=3)
        self.assertFalse(result["ok"])
        self.assertIn("more than 3 redirects", result["error"])

    def test_a_redirect_into_a_blocked_address_is_refused(self):
        # The first hop is allowed, the second is a metadata endpoint. Validating
        # only the URL the caller typed would walk straight into it.
        result = self.get("/offsite")
        self.assertFalse(result["ok"])
        self.assertIn("blocked target", result["error"])


class TestErrorStatuses(ServerCase):
    def test_a_404_is_a_result_not_an_exception(self):
        result = self.get("/gone")
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], 404)

    def test_an_unusual_status_still_returns_its_body(self):
        result = self.get("/teapot")
        self.assertEqual(result["status"], 418)
        self.assertIn("stout", result["text"])

    def test_a_closed_port_fails_cleanly(self):
        result = fetch("http://127.0.0.1:1/", allow_private=True, timeout=5)
        self.assertFalse(result["ok"])
        self.assertIn("error", result)


class TestGuardStillApplies(ServerCase):
    def test_without_allow_private_the_same_url_is_refused(self):
        with self.assertRaises(UrlNotAllowed):
            fetch(self.base + "/", timeout=5)


class TestDecoding(unittest.TestCase):
    def test_the_header_charset_wins_when_it_is_right(self):
        decoded = decode_body("café".encode("utf-8"), "text/html; charset=utf-8")
        self.assertEqual(decoded["text"], "café")
        self.assertEqual(decoded["encoding_source"], "content-type header")

    def test_a_meta_charset_is_used_when_the_header_is_silent(self):
        body = "<meta charset='iso-8859-1'>café".encode("latin-1")
        decoded = decode_body(body, "")
        self.assertEqual(decoded["encoding_source"], "meta charset")
        self.assertIn("café", decoded["text"])

    def test_a_lying_header_falls_through_to_something_readable(self):
        # Declared utf-8, actually latin-1: the bytes are invalid utf-8, so the
        # fallback chain has to catch it rather than raising.
        decoded = decode_body("café".encode("latin-1"), "text/html; charset=utf-8")
        self.assertIn("caf", decoded["text"])
        self.assertNotEqual(decoded["encoding_source"], "content-type header")

    def test_an_unknown_charset_name_does_not_crash(self):
        decoded = decode_body(b"plain text", "text/html; charset=not-a-real-encoding")
        self.assertEqual(decoded["text"], "plain text")

    def test_empty_body(self):
        self.assertEqual(decode_body(b"", "text/html")["text"], "")


if __name__ == "__main__":
    unittest.main()
