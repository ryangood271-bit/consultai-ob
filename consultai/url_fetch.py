"""Fetch a web page's visible text for the income-statement importer.

Only used as a convenience to avoid manual copy/paste. Includes basic SSRF guards (blocks
localhost/private/internal addresses) since this is a server making an outbound request based
on user input, even though the app only runs locally for this project.
"""

from __future__ import annotations

import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests

ALLOWED_SCHEMES = {"http", "https"}
USER_AGENT = "Mozilla/5.0 (compatible; ConsultAI-OB-Project/1.0; educational use)"
MAX_CHARS = 40000


class UrlFetchError(Exception):
    pass


class _VisibleTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self._chunks.append(text)

    def get_text(self) -> str:
        return "\n".join(self._chunks)


def _assert_safe_host(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UrlFetchError("Only http:// and https:// URLs are supported.")
    host = parsed.hostname
    if not host:
        raise UrlFetchError("Could not parse a hostname from that URL.")
    if host in ("localhost", "0.0.0.0") or host.startswith("127."):
        raise UrlFetchError("Local addresses are not allowed.")
    try:
        resolved = socket.gethostbyname(host)
        ip = ipaddress.ip_address(resolved)
    except (socket.gaierror, ValueError) as e:
        raise UrlFetchError(f"Could not resolve host '{host}': {e}") from e
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise UrlFetchError("That URL resolves to a private/internal address, which is not allowed.")
    return host


def fetch_url_text(url: str, max_chars: int = MAX_CHARS) -> str:
    """Fetch a URL and return its visible text, stripped of scripts/styles/tags.

    Raises UrlFetchError for disallowed URLs, network failures, or pages with no extractable
    text (e.g. pages that only render their content via client-side JavaScript).
    """
    _assert_safe_host(url)

    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise UrlFetchError(f"Could not fetch that URL: {e}") from e

    parser = _VisibleTextExtractor()
    parser.feed(response.text)
    text = parser.get_text()

    if not text.strip():
        raise UrlFetchError(
            "No readable text was found at that URL. Some sites (e.g. macrotrends.net, wsj.com) "
            "render their tables with JavaScript, which a direct fetch can't see — try "
            "stockanalysis.com instead, or paste the text/upload a PDF."
        )

    return text[:max_chars]
