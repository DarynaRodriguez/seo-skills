"""HTTP fetching, with the redirect chain kept because SEO lives in the redirects.

Standard library only: urllib, gzip, zlib. No requests, no httpx, nothing to
install. Every hop is validated by safety.validate_url before a socket opens.
"""
from __future__ import annotations

import gzip
import io
import re
import time
import zlib
from email.message import Message
from typing import Dict, List
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin

from .safety import UrlNotAllowed, validate_url

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; seo-skills/0.2; +https://github.com/DarynaRodriguez/seo-skills)"
)
DEFAULT_TIMEOUT = 20.0
MAX_REDIRECTS = 10
MAX_BYTES = 8 * 1024 * 1024

_META_CHARSET = re.compile(
    rb"<meta[^>]+charset\s*=\s*[\"\']?\s*([a-zA-Z0-9_.:-]+)", re.I
)


class FetchError(RuntimeError):
    """A fetch that could not produce a response at all."""


def _decompress(body: bytes, encoding: str) -> bytes:
    encoding = (encoding or "").lower().strip()
    if not body:
        return body
    try:
        if encoding == "gzip":
            return gzip.GzipFile(fileobj=io.BytesIO(body)).read()
        if encoding == "deflate":
            try:
                return zlib.decompress(body)
            except zlib.error:
                return zlib.decompress(body, -zlib.MAX_WBITS)
    except (OSError, zlib.error):
        # A server that mislabels its encoding is a finding, not a crash.
        return body
    return body


def decode_body(body: bytes, content_type: str) -> Dict[str, object]:
    """Decode bytes to text the way a browser would, and say how it was decided.

    Order: charset on the Content-Type header, then a meta charset in the first
    2 KB, then UTF-8, then cp1252 as the last resort. The chosen source is
    reported because a page whose declared and actual encoding disagree is a
    real defect and the caller should be able to see it.
    """
    declared = None
    if content_type:
        message = Message()
        message["content-type"] = content_type
        declared = message.get_param("charset")
    candidates: List[tuple] = []
    if declared:
        candidates.append((str(declared), "content-type header"))
    found = _META_CHARSET.search(body[:2048])
    if found:
        try:
            candidates.append((found.group(1).decode("ascii"), "meta charset"))
        except UnicodeDecodeError:
            pass
    candidates.append(("utf-8", "utf-8 fallback"))
    candidates.append(("cp1252", "cp1252 last resort"))

    for name, source in candidates:
        try:
            return {"text": body.decode(name), "encoding": name.lower(), "encoding_source": source}
        except (UnicodeDecodeError, LookupError):
            continue
    return {
        "text": body.decode("utf-8", errors="replace"),
        "encoding": "utf-8",
        "encoding_source": "utf-8 with replacement characters",
    }


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    """Hand redirects back to fetch() instead of following them silently."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    user_agent: str = DEFAULT_USER_AGENT,
    max_redirects: int = MAX_REDIRECTS,
    allow_private: bool = False,
    method: str = "GET",
    accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
) -> Dict[str, object]:
    """Fetch a URL, following redirects by hand so the chain is inspectable.

    Always returns a dict carrying `ok`. On a transport failure `ok` is False
    and `error` says why. There is no exception to catch for the ordinary case
    of a site being unreachable, because that is itself a finding.
    """
    chain: List[Dict[str, object]] = []
    current = validate_url(url, allow_private=allow_private)
    started = time.monotonic()

    for hop in range(max_redirects + 1):
        req = urlrequest.Request(
            current,
            method=method,
            headers={
                "User-Agent": user_agent,
                "Accept": accept,
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en;q=0.9,*;q=0.5",
            },
        )
        hop_started = time.monotonic()
        try:
            opener = urlrequest.build_opener(_NoRedirect)
            response = opener.open(req, timeout=timeout)
            status = response.status
            headers = dict(response.headers.items())
            raw = response.read(MAX_BYTES + 1)
            response.close()
        except HTTPError as exc:
            # A 4xx or 5xx is an answer, not a failure: the body and headers of
            # an error page are exactly what an audit needs to look at.
            status = exc.code
            headers = dict(exc.headers.items()) if exc.headers else {}
            try:
                raw = exc.read(MAX_BYTES + 1)
            except Exception:
                raw = b""
            finally:
                exc.close()
        except (URLError, OSError, ValueError) as exc:
            reason = getattr(exc, "reason", exc)
            return {
                "ok": False,
                "url": url,
                "final_url": current,
                "error": "{}: {}".format(type(exc).__name__, reason),
                "redirect_chain": chain,
                "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
            }

        truncated = len(raw) > MAX_BYTES
        raw = raw[:MAX_BYTES]
        hop_ms = round((time.monotonic() - hop_started) * 1000, 1)
        location = headers.get("Location") or headers.get("location")

        if status in (301, 302, 303, 307, 308) and location:
            target = urljoin(current, location.strip())
            chain.append(
                {"url": current, "status": status, "location": target, "elapsed_ms": hop_ms}
            )
            if hop == max_redirects:
                return {
                    "ok": False,
                    "url": url,
                    "final_url": current,
                    "error": "more than {} redirects".format(max_redirects),
                    "redirect_chain": chain,
                    "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
                }
            try:
                current = validate_url(target, allow_private=allow_private)
            except UrlNotAllowed as exc:
                return {
                    "ok": False,
                    "url": url,
                    "final_url": current,
                    "error": "redirect to a blocked target: {}".format(exc),
                    "redirect_chain": chain,
                    "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
                }
            continue

        encoding_header = headers.get("Content-Encoding") or headers.get("content-encoding") or ""
        body = _decompress(raw, encoding_header)
        content_type = headers.get("Content-Type") or headers.get("content-type") or ""
        decoded = decode_body(body, content_type)
        chain.append({"url": current, "status": status, "location": None, "elapsed_ms": hop_ms})
        return {
            "ok": True,
            "url": url,
            "final_url": current,
            "status": status,
            "headers": headers,
            "body": body,
            "text": decoded["text"],
            "encoding": decoded["encoding"],
            "encoding_source": decoded["encoding_source"],
            "bytes": len(body),
            "truncated": truncated,
            "redirect_chain": chain,
            "redirect_count": len(chain) - 1,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
        }
    raise FetchError("redirect loop escaped the hop counter")


SEO_HEADERS = (
    "content-type",
    "content-encoding",
    "cache-control",
    "x-robots-tag",
    "link",
    "content-language",
    "vary",
    "server",
    "strict-transport-security",
)


def public_summary(result: Dict[str, object]) -> Dict[str, object]:
    """The parts of a fetch result worth printing: no raw bytes, SEO headers only."""
    if not result.get("ok"):
        return {
            key: result[key]
            for key in ("ok", "url", "final_url", "error", "redirect_chain", "elapsed_ms")
            if key in result
        }
    headers = {str(k).lower(): v for k, v in (result.get("headers") or {}).items()}
    summary = {
        key: result[key]
        for key in (
            "ok",
            "url",
            "final_url",
            "status",
            "redirect_count",
            "redirect_chain",
            "bytes",
            "truncated",
            "encoding",
            "encoding_source",
            "elapsed_ms",
        )
    }
    summary["headers"] = {k: headers[k] for k in SEO_HEADERS if k in headers}
    return summary
