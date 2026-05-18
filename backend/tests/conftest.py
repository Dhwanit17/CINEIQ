"""Test fixtures."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cineiq.data.loader import Dataset


@pytest.fixture(scope="session")
def tiny_dataset() -> Dataset:
    """A 30-movie, 40-user synthetic dataset.

    Just enough density that SVD doesn't degenerate. Movies are clustered
    into two clear groups (sci-fi vs comedy) so the content model should
    produce sensible neighbors that tests can assert on.
    """
    rng = np.random.default_rng(0)

    sci_fi = [(i, f"SciFi Title {i}", 2000 + i % 20, "Sci-Fi Action")
              for i in range(1, 16)]
    comedy = [(i + 100, f"Comedy Title {i}", 1990 + i % 25, "Comedy Romance")
              for i in range(1, 16)]
    rows = sci_fi + comedy
    movies = pd.DataFrame(rows, columns=["movie_id", "title", "year", "genres"])
    movies["content_text"] = movies["title"] + " " + movies["year"].astype(str) + " " + movies["genres"]

    # 40 users — half love sci-fi, half love comedy. Some cross-tasters in the middle.
    user_ids = list(range(1, 41))
    records = []
    for u in user_ids:
        loves_scifi = u <= 25  # overlap zone
        for mid in movies["movie_id"]:
            if rng.random() > 0.4:  # sparsity
                continue
            is_scifi = mid < 100
            if loves_scifi:
                r = rng.integers(4, 6) if is_scifi else rng.integers(1, 4)
            else:
                r = rng.integers(4, 6) if not is_scifi else rng.integers(1, 4)
            records.append((u, int(mid), int(r), 0))
    ratings = pd.DataFrame(records, columns=["user_id", "movie_id", "rating", "timestamp"])
    return Dataset(ratings=ratings, movies=movies)
