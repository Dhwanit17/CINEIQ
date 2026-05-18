"""Tests for the data loader, including regression coverage for NA handling."""
from __future__ import annotations

import pandas as pd
import pytest

from cineiq.data.loader import _load_ml100k, Dataset


def test_loader_handles_missing_year(tmp_path):
    """
    Regression: pd.isna(row['year']) must be used in content_text, not
    Python truthiness. Some ml-100k rows have a title without a parseable
    `(YYYY)` suffix — without the fix, the loader crashed with
    'boolean value of NA is ambiguous'.
    """
    root = tmp_path / "ml-100k"
    root.mkdir()

    # u.data: tab-separated, 4 cols
    (root / "u.data").write_text(
        "1\t1\t5\t881250949\n"
        "1\t2\t3\t881250949\n"
        "2\t1\t4\t881250949\n"
    )

    # u.item: pipe-separated, latin-1. Movie 1 has a year, movie 2 deliberately
    # doesn't — this is the failure case. 19 trailing genre flags.
    genre_flags = "|".join(["0"] * 19)
    rows = [
        f"1|Toy Story (1995)|01-Jan-1995||http://...|{genre_flags.replace('0', '1', 1)}",
        f"2|unknown||||{ '|'.join(['0']*19) }",
    ]
    (root / "u.item").write_text("\n".join(rows) + "\n", encoding="latin-1")

    # Should not raise
    ds: Dataset = _load_ml100k(root)
    assert len(ds.movies) == 2

    # The row with no year should have a non-empty content_text built from the title alone
    no_year_row = ds.movies.loc[ds.movies["movie_id"] == 2].iloc[0]
    assert pd.isna(no_year_row["year"])
    assert "unknown" in no_year_row["content_text"]
    # Critically: no literal "NA" or "<NA>" string leaked in
    assert "<NA>" not in no_year_row["content_text"]
    assert "NA" not in no_year_row["content_text"].split()
