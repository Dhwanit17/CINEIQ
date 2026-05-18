"""
MovieLens loader.

Returns three things:
  - ratings: DataFrame[user_id, movie_id, rating, timestamp]
  - movies:  DataFrame[movie_id, title, year, genres, content_text]
  - id_maps: helpers to go title <-> movie_id

The `content_text` column is a single denormalized string used by the
TF-IDF content model: "<title> <year> <genres>". For 25M we'd append
tags/keywords from the genome scores.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from cineiq.config import DatasetConfig, settings

# ml-100k genre columns are 19 unnamed binary columns after the date fields.
ML100K_GENRES = [
    "unknown", "Action", "Adventure", "Animation", "Children", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
]


@dataclass(frozen=True)
class Dataset:
    """In-memory dataset bundle. All DataFrames; no I/O after construction."""

    ratings: pd.DataFrame
    movies: pd.DataFrame

    @property
    def n_users(self) -> int:
        return int(self.ratings["user_id"].nunique())

    @property
    def n_movies(self) -> int:
        return len(self.movies)

    @property
    def n_ratings(self) -> int:
        return len(self.ratings)

    def title_to_id(self, title: str) -> int | None:
        """Case-insensitive exact lookup. Returns None if not found."""
        mask = self.movies["title"].str.lower() == title.lower()
        hits = self.movies.loc[mask, "movie_id"]
        return int(hits.iloc[0]) if len(hits) else None

    def search_titles(self, query: str, limit: int = 10) -> pd.DataFrame:
        """Substring search, case-insensitive. For the API's autocomplete."""
        mask = self.movies["title"].str.contains(query, case=False, na=False, regex=False)
        return self.movies.loc[mask].head(limit)


# ---------------------------------------------------------------------------
# ml-100k loader
# ---------------------------------------------------------------------------

def _load_ml100k(root: Path) -> Dataset:
    """Load the ml-100k flat-file format."""
    if not root.exists():
        raise FileNotFoundError(
            f"MovieLens 100K not found at {root}. "
            f"Run: python -m cineiq.data.download"
        )

    # Ratings: tab-separated, no header
    ratings = pd.read_csv(
        root / "u.data",
        sep="\t",
        names=["user_id", "movie_id", "rating", "timestamp"],
        engine="c",
    )

    # Movies: pipe-separated, latin-1, no header
    movie_cols = ["movie_id", "title", "release_date", "video_release", "imdb_url"] + ML100K_GENRES
    movies_raw = pd.read_csv(
        root / "u.item",
        sep="|",
        names=movie_cols,
        encoding="latin-1",
        engine="c",
    )

    # Pull year out of the title (ml-100k titles look like "Toy Story (1995)")
    movies_raw["year"] = movies_raw["title"].str.extract(r"\((\d{4})\)\s*$").astype("Int64")

    # Collapse one-hot genre columns into a single space-joined string
    def genre_string(row: pd.Series) -> str:
        return " ".join(g for g in ML100K_GENRES if row[g] == 1 and g != "unknown")

    movies_raw["genres"] = movies_raw.apply(genre_string, axis=1)

    # Build the content_text used by TF-IDF.
    # `year` is Int64 (pandas nullable int), so missing values are pd.NA.
    # We can't use truthiness on NA, so check explicitly with pd.isna.
    def content_text(row: pd.Series) -> str:
        title = "" if pd.isna(row["title"]) else str(row["title"])
        year = "" if pd.isna(row["year"]) else str(int(row["year"]))
        genres = row["genres"] or ""
        return " ".join(p for p in (title, year, genres) if p).strip()

    movies_raw["content_text"] = movies_raw.apply(content_text, axis=1)

    movies = movies_raw[["movie_id", "title", "year", "genres", "content_text"]].copy()
    return Dataset(ratings=ratings, movies=movies)


# ---------------------------------------------------------------------------
# ml-25m loader (stub — same interface, different format)
# ---------------------------------------------------------------------------

def _load_ml25m(root: Path) -> Dataset:
    """Load ml-25m. CSV-based, larger, has tag genome."""
    if not root.exists():
        raise FileNotFoundError(
            f"MovieLens 25M not found at {root}. "
            f"Run: python -m cineiq.data.download --variant ml-25m"
        )

    ratings = pd.read_csv(root / "ratings.csv").rename(
        columns={"userId": "user_id", "movieId": "movie_id"}
    )
    movies_raw = pd.read_csv(root / "movies.csv").rename(columns={"movieId": "movie_id"})

    movies_raw["year"] = movies_raw["title"].str.extract(r"\((\d{4})\)\s*$").astype("Int64")
    movies_raw["genres"] = movies_raw["genres"].str.replace("|", " ", regex=False)
    movies_raw["content_text"] = (
        movies_raw["title"].fillna("")
        + " "
        + movies_raw["year"].astype("string").fillna("")
        + " "
        + movies_raw["genres"].fillna("")
    )
    movies = movies_raw[["movie_id", "title", "year", "genres", "content_text"]].copy()
    return Dataset(ratings=ratings, movies=movies)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

_LOADERS = {
    "ml-100k": _load_ml100k,
    "ml-25m": _load_ml25m,
    "ml-latest-small": _load_ml25m,  # same CSV format as 25M
}


@lru_cache(maxsize=4)
def load_dataset(variant: str | None = None) -> Dataset:
    """Load and cache a dataset. Pass None to use the configured default."""
    cfg: DatasetConfig = settings.dataset
    v = variant or cfg.variant
    if v not in _LOADERS:
        raise ValueError(f"Unsupported variant {v!r}. Add a loader in cineiq/data/loader.py")
    return _LOADERS[v](DATA_DIR_OF(v))


def DATA_DIR_OF(variant: str) -> Path:
    from cineiq.config import DATA_DIR
    return DATA_DIR / variant
