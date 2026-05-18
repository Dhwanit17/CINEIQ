"""
Download the TMDB 5000 movies dataset.

We pull the two CSVs from a public mirror of the original Kaggle dump,
avoiding kagglehub (which requires API credentials and a Kaggle account).

The data is identical across mirrors — it's the TMDB 5000 snapshot that's
been circulating since 2017. We try several mirrors in case one is
unreachable; the script succeeds as soon as one works for each file.

Usage:
    python -m cineiq.data.download_tmdb
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

from cineiq.config import DATA_DIR

# Multiple mirrors per file. We try them in order and accept the first
# that returns 200. The harshitcodes repo is the canonical source for
# both CSVs in this format; the others are insurance against link rot.
TMDB_MIRRORS: dict[str, list[str]] = {
    "tmdb_5000_movies.csv": [
        "https://raw.githubusercontent.com/harshitcodes/tmdb_movie_data_analysis/master/tmdb-5000-movie-dataset/tmdb_5000_movies.csv",
        "https://raw.githubusercontent.com/vamshi121/TMDB-5000-Movie-Dataset/main/tmdb_5000_movies.csv",
        "https://media.githubusercontent.com/media/harshitcodes/tmdb_movie_data_analysis/master/tmdb-5000-movie-dataset/tmdb_5000_movies.csv",
    ],
    "tmdb_5000_credits.csv": [
        "https://raw.githubusercontent.com/harshitcodes/tmdb_movie_data_analysis/master/tmdb-5000-movie-dataset/tmdb_5000_credits.csv",
        "https://media.githubusercontent.com/media/harshitcodes/tmdb_movie_data_analysis/master/tmdb-5000-movie-dataset/tmdb_5000_credits.csv",
    ],
}


def _try_download(url: str, out_path: Path) -> bool:
    """Try one mirror. Returns True on success, False to let the caller try the next."""
    try:
        resp = requests.get(url, stream=True, timeout=120, allow_redirects=True)
    except requests.RequestException as exc:
        print(f"  [skip mirror] {exc}")
        return False

    if resp.status_code != 200:
        print(f"  [skip mirror] HTTP {resp.status_code}")
        return False

    # Some "raw" hosts (like media.githubusercontent.com for LFS) return HTML
    # error pages with 200 if the file isn't real. Sanity check: CSV should
    # start with text content, not "<!DOCTYPE" or "<html".
    chunks = []
    total = int(resp.headers.get("content-length") or 0)
    downloaded = 0
    first_bytes = b""
    for chunk in resp.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        if not first_bytes:
            first_bytes = chunk[:200]
            lower = first_bytes.lower()
            if lower.startswith(b"<!doctype") or lower.startswith(b"<html"):
                print("  [skip mirror] got HTML, not CSV")
                return False
        chunks.append(chunk)
        downloaded += len(chunk)
        if total:
            pct = downloaded / total * 100
            print(f"\r  {downloaded / 1e6:.1f} / {total / 1e6:.1f} MB ({pct:.0f}%)", end="")
    print()

    if downloaded < 1024:
        print("  [skip mirror] file too small, looks bogus")
        return False

    with out_path.open("wb") as f:
        for chunk in chunks:
            f.write(chunk)
    return True


def download(force: bool = False) -> Path:
    target_dir = DATA_DIR / "tmdb"
    target_dir.mkdir(parents=True, exist_ok=True)

    for filename, urls in TMDB_MIRRORS.items():
        out_path = target_dir / filename
        if out_path.exists() and not force:
            print(f"[skip] {out_path} already exists ({out_path.stat().st_size / 1e6:.1f} MB)")
            continue

        succeeded = False
        for url in urls:
            print(f"[get] {filename}  <-  {url}")
            if _try_download(url, out_path):
                succeeded = True
                break

        if not succeeded:
            raise RuntimeError(
                f"Could not download {filename} from any mirror. "
                f"Last URLs tried: {urls}. "
                f"You can manually place the CSVs in {target_dir} and re-run."
            )

    print(f"[done] {target_dir}")
    return target_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download TMDB 5000 dataset")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    download(force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
