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
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
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
        pass
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
