"""Every command must fail cleanly, never with a traceback.

A traceback at a user who mistyped a scheme is the difference between a tool that
feels finished and one that does not. Found in an audit: `robots ftp://...` and
`sitemap notaurl` both crashed, because they call fetch directly rather than
through the helper that catches a refused URL.
"""
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from seo_tools.cli import main

# Inputs a user will get wrong, and inputs an attacker would try.
BAD_URLS = [
    "notaurl",
    "example.com",
    "ftp://example.com/",
    "file:///etc/passwd",
    "javascript:alert(1)",
    "http://localhost/admin",
    "http://127.0.0.1/",
    "http://169.254.169.254/latest/meta-data/",
    "http://user:pass@example.com/",
    "",
]
URL_COMMANDS = ["page", "fetch", "meta", "headings", "schema", "robots", "sitemap"]


def run(argv):
    """Run the CLI, swallowing output, and return the exit code."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            return main(argv), out.getvalue() + err.getvalue()
    except SystemExit as exc:
        return int(exc.code or 0), out.getvalue() + err.getvalue()


class TestNoTracebackOnBadUrl(unittest.TestCase):
    def test_every_url_command_refuses_every_bad_url_cleanly(self):
        for command in URL_COMMANDS:
            for url in BAD_URLS:
                with self.subTest(command=command, url=url):
                    code, output = run([command, url])
                    self.assertNotEqual(code, 0, "{} accepted {!r}".format(command, url))
                    self.assertNotIn("Traceback", output)

    def test_the_json_form_reports_the_refusal_as_data(self):
        import json

        code, output = run(["robots", "ftp://example.com/", "--json"])
        self.assertEqual(code, 1)
        payload = json.loads(output)
        self.assertIs(payload["ok"], False)
        self.assertIn("ftp", payload["error"])

    def test_a_missing_file_is_a_clean_failure_too(self):
        for command in ("crawl", "gsc"):
            with self.subTest(command=command):
                code, output = run([command, "no-such-file-here.csv"])
                self.assertEqual(code, 1)
                self.assertNotIn("Traceback", output)

    def test_no_arguments_is_a_usage_error_not_a_crash(self):
        for command in URL_COMMANDS + ["crawl", "gsc", "baseline", "drift", "history"]:
            with self.subTest(command=command):
                code, output = run([command])
                self.assertEqual(code, 2, "{} did not report a usage error".format(command))
                self.assertNotIn("Traceback", output)


if __name__ == "__main__":
    unittest.main()
