from unittest.mock import MagicMock, patch

import pytest

from consultai import url_fetch


def test_rejects_non_http_scheme():
    with pytest.raises(url_fetch.UrlFetchError):
        url_fetch.fetch_url_text("ftp://example.com/file.csv")


def test_rejects_localhost():
    with pytest.raises(url_fetch.UrlFetchError):
        url_fetch.fetch_url_text("http://localhost:8501/secret")


def test_rejects_loopback_ip():
    with pytest.raises(url_fetch.UrlFetchError):
        url_fetch.fetch_url_text("http://127.0.0.1/admin")


def test_extracts_visible_text_and_strips_scripts(monkeypatch):
    html = """
    <html><head><style>.x{color:red}</style><script>evil()</script></head>
    <body><h1>Revenue</h1><p>Operating Income 11,965</p></body></html>
    """
    fake_response = MagicMock()
    fake_response.text = html
    fake_response.raise_for_status = MagicMock()

    with patch("consultai.url_fetch._assert_safe_host", return_value="example.com"):
        with patch("requests.get", return_value=fake_response):
            text = url_fetch.fetch_url_text("https://example.com/income-statement")
            assert "Operating Income" in text
            assert "evil()" not in text
            assert "color:red" not in text


def test_empty_page_raises():
    fake_response = MagicMock()
    fake_response.text = "<html><body><script>onlyJsContent()</script></body></html>"
    fake_response.raise_for_status = MagicMock()

    with patch("consultai.url_fetch._assert_safe_host", return_value="example.com"):
        with patch("requests.get", return_value=fake_response):
            with pytest.raises(url_fetch.UrlFetchError):
                url_fetch.fetch_url_text("https://example.com/js-only-page")
