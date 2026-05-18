"""
Download the MovieLens 100K dataset.

Usage:
    python -m cineiq.data.download
    python -m cineiq.data.download --variant ml-25m

100K is ~5 MB and downloads in seconds. 25M is ~265 MB.
"""
from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import requests

from cineiq.config import DATA_DIR

URLS = {
    "ml-100k": "https://files.grouplens.org/datasets/movielens/ml-100k.zip",
    "ml-25m": "https://files.grouplens.org/datasets/movielens/ml-25m.zip",
    "ml-latest-small": "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip",
}


def download(variant: str = "ml-100k", force: bool = False) -> Path:
    """Download and unzip a MovieLens variant into data/. Returns the extracted dir."""
    if variant not in URLS:
        raise ValueError(f"Unknown variant {variant!r}. Pick from: {list(URLS)}")

    target = DATA_DIR / variant
    if target.exists() and not force:
        print(f"[skip] {target} already exists. Use --force to re-download.")
        return target

    url = URLS[variant]
    print(f"[get] {url}")
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()

    buf = io.BytesIO()
    total = int(resp.headers.get("content-length") or 0)
    downloaded = 0
    for chunk in resp.iter_content(chunk_size=64 * 1024):
        buf.write(chunk)
        downloaded += len(chunk)
        if total:
            pct = downloaded / total * 100
            print(f"\r  {downloaded / 1e6:.1f} / {total / 1e6:.1f} MB ({pct:.0f}%)", end="")
    print()

    print(f"[unzip] -> {DATA_DIR}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(buf) as z:
        z.extractall(DATA_DIR)

    print(f"[done] {target}")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download MovieLens dataset")
    parser.add_argument("--variant", default="ml-100k", choices=list(URLS))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    download(args.variant, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
