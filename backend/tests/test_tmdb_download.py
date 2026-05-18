"""Tests for the TMDB downloader's fallback behavior."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cineiq.data import download_tmdb


class _FakeResp:
    """Minimal requests.Response-like object."""
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status_code = status
        self.headers = {"content-length": str(len(body))}

    def iter_content(self, chunk_size: int = 64 * 1024):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i:i + chunk_size]


def test_html_response_is_rejected(tmp_path: Path):
    """If a mirror returns an HTML error page with 200, we must skip it."""
    out = tmp_path / "fake.csv"
    html = b"<!DOCTYPE html><html><body>Not Found</body></html>" + b"x" * 2000
    with patch("cineiq.data.download_tmdb.requests.get", return_value=_FakeResp(html, 200)):
        result = download_tmdb._try_download("http://fake", out)
    assert result is False
    assert not out.exists()


def test_real_csv_response_succeeds(tmp_path: Path):
    out = tmp_path / "fake.csv"
    body = b"movie_id,title,cast,crew\n1,Test,actor,director\n" * 100
    with patch("cineiq.data.download_tmdb.requests.get", return_value=_FakeResp(body, 200)):
        result = download_tmdb._try_download("http://fake", out)
    assert result is True
    assert out.exists()
    assert out.stat().st_size > 1024


def test_404_skips_to_next_mirror(tmp_path: Path):
    """A 404 response should return False so the loop tries the next mirror."""
    out = tmp_path / "fake.csv"
    with patch("cineiq.data.download_tmdb.requests.get", return_value=_FakeResp(b"", 404)):
        result = download_tmdb._try_download("http://fake", out)
    assert result is False


def test_network_exception_skips_to_next_mirror(tmp_path: Path):
    out = tmp_path / "fake.csv"
    import requests as req
    with patch(
        "cineiq.data.download_tmdb.requests.get",
        side_effect=req.ConnectionError("DNS fail"),
    ):
        result = download_tmdb._try_download("http://fake", out)
    assert result is False


def test_too_small_response_is_rejected(tmp_path: Path):
    """A response that succeeds but returns 50 bytes is suspect."""
    out = tmp_path / "fake.csv"
    body = b"title,id\nfoo,1\n"  # under 1 KB
    with patch("cineiq.data.download_tmdb.requests.get", return_value=_FakeResp(body, 200)):
        result = download_tmdb._try_download("http://fake", out)
    assert result is False
