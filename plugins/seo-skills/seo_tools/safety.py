"""URL validation. Every network call in this package goes through validate_url first.

The scripts here take URLs from whoever is driving the agent, which means a
crafted URL could otherwise reach a metadata endpoint or something on the
loopback interface. So: scheme allowlist, no credentials in the URL, and every
address the hostname resolves to has to be a public one. Redirects get checked
again at each hop, because the first hop being public says nothing about the
second.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from typing import List, Tuple
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ALLOWED_SCHEMES = ("http", "https")

# Hostnames that never resolve to anything a caller should reach.
BLOCKED_HOST_SUFFIXES = (
    ".local",
    ".localhost",
    ".internal",
    ".home.arpa",
)
BLOCKED_HOSTS = ("localhost", "metadata.google.internal")

# Cloud instance metadata. Link-local covers 169.254.169.254 already, but naming
# these makes the intent legible to anyone reading a denial.
METADATA_ADDRESSES = ("169.254.169.254", "fd00:ec2::254", "100.100.100.200")

# Any C0 control character, DEL, or a Unicode line or paragraph separator. The
# null byte matters most: getaddrinfo truncates at it, so a hostname carrying one
# is checked as its prefix and written as the whole string. CR and LF are the
# classic request-smuggling shapes.
CONTROL_CHARS = re.compile("[" + "".join(chr(c) for c in list(range(0x20)) + [0x7f]) + "\u2028\u2029]")

# Hostnames that are a number in disguise. Resolvers disagree about these:
# getaddrinfo on macOS accepts octal and short forms that fail on Windows, so
# leaving it to the resolver means the guard works by accident on one platform
# and not at all on another. CI caught exactly that, on 0177.0.0.1. If a host
# looks numeric it has to parse as a valid address or be refused, because there
# is no way to know which interpretation the connection will use.
NUMERIC_HOST = re.compile(
    r"^(?:"
    r"[0-9]+"                # a bare integer, 2130706433
    r"|0[xX][0-9a-fA-F]+"    # hex, 0x7f000001
    r"|[0-9.]+"              # dotted numeric: octal 0177.0.0.1, short form 127.1
    r")$"
)

# Query parameters that identify a campaign, not a page. Stripped when
# normalising so the same page tracked twice matches itself.
TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = (
    "gclid",
    "fbclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "ref",
    "ref_src",
    "_hsenc",
    "_hsmi",
    "hsctatracking",
    "yclid",
    "twclid",
    "ttclid",
    "vero_id",
    "wickedid",
)


class UrlNotAllowed(ValueError):
    """Raised when a URL fails validation. The message says which rule tripped."""


def _is_public_address(raw: str) -> bool:
    try:
        addr = ipaddress.ip_address(raw)
    except ValueError:
        return False
    if raw in METADATA_ADDRESSES:
        return False

    # Judge an IPv4-mapped IPv6 address as its IPv4 form. Python 3.13 taught
    # is_private and is_loopback to look through the mapping; earlier versions do
    # not, so ::ffff:127.0.0.1 is classified differently depending on the
    # interpreter. Unmapping here makes every version agree, and agreeing is the
    # point: a guard that changes behaviour with the runtime is not one.
    mapped = getattr(addr, "ipv4_mapped", None)
    if mapped is not None:
        addr = mapped
        if str(addr) in METADATA_ADDRESSES:
            return False
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
        # is_global additionally excludes shared address space (100.64.0.0/10,
        # carrier-grade NAT), benchmarking and documentation ranges. Kept
        # alongside the explicit checks rather than replacing them, because
        # is_global reports multicast as global.
        or not addr.is_global
    )


def resolve_host(host: str) -> List[str]:
    """Every address a hostname resolves to. Raises UrlNotAllowed if DNS fails."""
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UrlNotAllowed("hostname {!r} does not resolve ({})".format(host, exc.strerror or exc))
    seen = []
    for info in infos:
        address = info[4][0]
        if address not in seen:
            seen.append(address)
    if not seen:
        raise UrlNotAllowed("hostname {!r} resolves to no addresses".format(host))
    return seen


def validate_url(url: str, allow_private: bool = False) -> str:
    """Return the URL unchanged if it is safe to fetch, else raise UrlNotAllowed.

    allow_private exists so the test suite can serve fixtures on 127.0.0.1. No
    command-line flag sets it and nothing in cli.py passes it.

    It relaxes exactly one rule: the private-address range check. The scheme
    allowlist, the credential ban, local hostnames and cloud metadata addresses
    stay blocked either way. That distinction matters because fetch() carries
    this flag through to every redirect hop, so a broader escape hatch would let
    a fixture server redirect a test into a metadata endpoint.
    """
    if not isinstance(url, str) or not url.strip():
        raise UrlNotAllowed("empty URL")
    found = CONTROL_CHARS.search(url)
    if found:
        raise UrlNotAllowed(
            "URL contains a control character ({!r}), which is refused because the "
            "resolver and the request would disagree about the hostname".format(
                found.group(0)
            )
        )
    parts = urlsplit(url.strip())

    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise UrlNotAllowed(
            "scheme {!r} is not allowed, use http or https".format(parts.scheme or "(none)")
        )
    if parts.username or parts.password:
        raise UrlNotAllowed("credentials in the URL are not allowed")
    host = parts.hostname
    if not host:
        raise UrlNotAllowed("no hostname in {!r}".format(url))
    host = host.lower().rstrip(".")

    # Never relaxed, not even for tests.
    if host in BLOCKED_HOSTS or host.endswith(BLOCKED_HOST_SUFFIXES):
        raise UrlNotAllowed("hostname {!r} is a local name".format(host))
    if host in METADATA_ADDRESSES:
        raise UrlNotAllowed("address {} is a cloud metadata endpoint".format(host))

    # A bare IP in the URL: check it directly, no DNS involved.
    try:
        ipaddress.ip_address(host)
    except ValueError:
        # Not a valid address. If it nonetheless looks like a number, refuse it
        # rather than handing an ambiguous string to the resolver.
        if NUMERIC_HOST.match(host):
            raise UrlNotAllowed(
                "hostname {!r} looks like a numeric address but is not a valid one. "
                "Resolvers disagree about forms like this, so it is refused rather "
                "than guessed at.".format(host)
            )
    else:
        if not allow_private and not _is_public_address(host):
            raise UrlNotAllowed("address {} is not a public address".format(host))
        return url.strip()

    if allow_private:
        return url.strip()

    for address in resolve_host(host):
        if not _is_public_address(address):
            raise UrlNotAllowed(
                "hostname {!r} resolves to {}, which is not a public address".format(host, address)
            )
    return url.strip()


def normalise_url(url: str) -> str:
    """A stable key for the same page seen twice.

    Lowercases scheme and host, drops the default port, drops the fragment,
    strips tracking parameters, sorts what is left, and removes a trailing
    slash on a non-empty path. Used for baseline matching, not for fetching.
    """
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower().rstrip(".")
    port = parts.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        host = "{}:{}".format(host, port)

    kept: List[Tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        low = key.lower()
        if low in TRACKING_PARAMS or low.startswith(TRACKING_PREFIXES):
            continue
        kept.append((key, value))
    query = urlencode(sorted(kept))

    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/") or "/"

    return urlunsplit((scheme, host, path, query, ""))


def redact(url: str) -> str:
    """A URL safe to print. Strips any userinfo so a password cannot reach a log.

    Error messages echo the URL they refused, which is useful, and a URL carrying
    credentials is exactly the case where echoing it is harmful. Redacting is
    cheaper than remembering not to print it.
    """
    if not isinstance(url, str):
        return "<not a string>"
    try:
        parts = urlsplit(url)
    except ValueError:
        return "<unparseable URL>"
    if not (parts.username or parts.password):
        return url
    host = parts.hostname or ""
    if parts.port:
        host = "{}:{}".format(host, parts.port)
    return urlunsplit((parts.scheme, "<redacted>@" + host, parts.path, parts.query, parts.fragment))
