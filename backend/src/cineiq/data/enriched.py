"""
TMDB-enriched dataset loader.

Joins MovieLens (which gives us ratings) with TMDB 5000 (which gives us
cast, crew, keywords, plot, production companies) and produces a single
DataFrame with a rich `tags` text column per movie.

This is the data backbone for the personalized models ported from the
notebooks. Movie-level item-item models keep using the simpler
`Dataset.movies` from `loader.py`.

Why a separate loader: TMDB is optional. Users who only want item-item
recommendation don't need to download 30 MB of TMDB data. Users who
want personalization do.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from cineiq.config import DATA_DIR, settings
from cineiq.data.loader import Dataset, load_dataset


@dataclass(frozen=True)
class EnrichedDataset:
    """MovieLens + TMDB joined. The movies frame has a rich `tags` column."""

    ratings: pd.DataFrame                 # user_id, movie_id, rating, timestamp
    movies: pd.DataFrame                  # movie_id, title, year, genres, tags

    @property
    def n_users(self) -> int:
        return int(self.ratings["user_id"].nunique())

    @property
    def n_movies(self) -> int:
        return int(self.movies["movie_id"].nunique())

    @property
    def n_ratings(self) -> int:
        return len(self.ratings)


# ---------------------------------------------------------------------------
# JSON-column parsers (lifted from the notebook, made safer)
# ---------------------------------------------------------------------------

def _parse_obj(x):
    """Parse a TMDB JSON-string column safely."""
    if isinstance(x, list):
        return x
    if pd.isna(x):
        return []
    try:
        return ast.literal_eval(x)
    except (ValueError, SyntaxError, TypeError):
        return []


def _get_names(lst, limit: int | None = None) -> list[str]:
    if not isinstance(lst, list):
        return []
    items = lst[:limit] if limit else lst
    return [d["name"] for d in items if isinstance(d, dict) and "name" in d]


def _get_director(lst) -> list[str]:
    if not isinstance(lst, list):
        return []
    for d in lst:
        if isinstance(d, dict) and d.get("job") == "Director":
            return [d.get("name") or ""]
    return []


def _squash(names: list[str]) -> list[str]:
    """Collapse 'Christopher Nolan' -> 'ChristopherNolan' so TF-IDF treats
    full names as single tokens instead of common first-name tokens."""
    return [n.replace(" ", "") for n in names if isinstance(n, str) and n.strip()]


def _list_to_text(lst) -> str:
    return " ".join(lst) if isinstance(lst, list) else ""


# Common articles that appear suffixed in MovieLens titles
# ("Postino, Il (1994)" -> "Il Postino"). We rotate them back to the
# front before joining to TMDB.
_TRAILING_ARTICLES = re.compile(
    r",\s+(the|a|an|il|la|le|les|los|las|el|der|die|das|l'|les)$",
    re.IGNORECASE,
)


def _normalize_title(title: str) -> str:
    """Clean a MovieLens or TMDB title for joining.

    - strip year suffix like "(1995)"
    - rotate trailing article: "Postino, Il" -> "Il Postino"
    - lowercase, strip whitespace, drop punctuation that varies between
      sources (apostrophes, periods, colons)
    """
    if not isinstance(title, str):
        return ""
    # Remove year suffix
    s = re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()
    # Rotate "Title, Article" -> "Article Title"
    m = _TRAILING_ARTICLES.search(s)
    if m:
        article = m.group(1)
        s = f"{article} {s[:m.start()]}".strip()
    # Lowercase and strip punctuation that varies (apostrophes, periods, etc.)
    s = s.lower()
    s = re.sub(r"[’'`.:;!?]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_enriched(variant: str | None = None) -> EnrichedDataset:
    """Load MovieLens + TMDB, joined, with rich per-movie tags.

    Raises FileNotFoundError if TMDB data hasn't been downloaded yet.
    The MovieLens variant is whatever is configured (or passed in).
    """
    tmdb_dir = DATA_DIR / "tmdb"
    if not tmdb_dir.exists():
        raise FileNotFoundError(
            f"TMDB data not found at {tmdb_dir}. "
            f"Run: python -m cineiq.data.download_tmdb"
        )

    # 1. Start with the MovieLens side (uses the existing loader).
    ml: Dataset = load_dataset(variant)

    # 2. Load TMDB
    movies_tmdb = pd.read_csv(tmdb_dir / "tmdb_5000_movies.csv")
    credits_tmdb = pd.read_csv(tmdb_dir / "tmdb_5000_credits.csv")
    movies_tmdb["tmdbId"] = movies_tmdb["id"]
    credits_tmdb["tmdbId"] = credits_tmdb["movie_id"]
    tmdb = pd.merge(
        movies_tmdb[["tmdbId", "genres", "keywords", "production_companies", "overview"]],
        credits_tmdb[["tmdbId", "cast", "crew"]],
        on="tmdbId",
        how="inner",
    )

    # 3. Join MovieLens movies <-> TMDB by movieId via links.csv if it
    # exists (MovieLens 25M / latest-small ships it). Falls back to
    # title-based join for ml-100k.
    ml_movies = ml.movies.copy()
    tmdb_by_id_map: pd.DataFrame | None = None
    links_path = (DATA_DIR / (variant or settings.dataset.variant) / "links.csv")
    if links_path.exists():
        try:
            links = pd.read_csv(links_path).rename(columns={"movieId": "movie_id", "tmdbId": "tmdbId"})
            links = links[["movie_id", "tmdbId"]].dropna()
            links["tmdbId"] = links["tmdbId"].astype("Int64")
            tmdb_by_id_map = links
            print(f"[enriched] using links.csv ({len(links)} rows)")
        except Exception as exc:
            print(f"[enriched] links.csv unreadable ({exc}); falling back to title join")

    if tmdb_by_id_map is not None:
        ml_movies = ml_movies.merge(tmdb_by_id_map, on="movie_id", how="left")
    else:
        # Title-based join, with rotated articles and stripped punctuation
        # to maximize hit rate.
        ml_movies["_title_clean"] = ml_movies["title"].apply(_normalize_title)
        movies_tmdb["_title_clean"] = movies_tmdb["title"].apply(_normalize_title)

        title_to_tmdb = (
            movies_tmdb[["_title_clean", "tmdbId"]]
            .drop_duplicates(subset="_title_clean", keep="first")
        )
        ml_movies = ml_movies.merge(title_to_tmdb, on="_title_clean", how="left")

    # Make sure tmdbId is a consistent dtype on both sides before merging
    ml_movies["tmdbId"] = pd.to_numeric(ml_movies["tmdbId"], errors="coerce")
    tmdb["tmdbId"] = pd.to_numeric(tmdb["tmdbId"], errors="coerce")
    joined = ml_movies.merge(tmdb, on="tmdbId", how="left")

    # 4. Parse TMDB JSON columns and build tag lists
    joined["tmdb_genres"] = joined["genres_y"].apply(_parse_obj).apply(_get_names).apply(_squash) \
        if "genres_y" in joined.columns else joined["genres"].apply(_parse_obj).apply(_get_names).apply(_squash)
    joined["tmdb_keywords"] = joined["keywords"].apply(_parse_obj).apply(_get_names).apply(_squash)
    joined["tmdb_cast"] = joined["cast"].apply(_parse_obj).apply(lambda x: _get_names(x, limit=5)).apply(_squash)
    joined["tmdb_director"] = joined["crew"].apply(_parse_obj).apply(_get_director).apply(_squash)
    joined["tmdb_prod"] = joined["production_companies"].apply(_parse_obj).apply(_get_names).apply(_squash)

    # 5. Build the tags string with notebook-style duplication for weighting.
    # genres ×3, keywords ×2, cast ×1, director ×2, prod ×1.
    # Also include the MovieLens genres so movies with no TMDB match still
    # have *something* searchable (this is what saves the rec quality on
    # films that didn't match TMDB).
    def build_tags(row: pd.Series) -> str:
        ml_genres = (row.get("genres_x") or row.get("genres") or "") if isinstance(row.get("genres_x"), str) else ""
        parts = [
            ml_genres,
            _list_to_text(row["tmdb_genres"]) * 1,  # will dup below
            _list_to_text(row["tmdb_genres"]),
            _list_to_text(row["tmdb_genres"]),
            _list_to_text(row["tmdb_keywords"]),
            _list_to_text(row["tmdb_keywords"]),
            _list_to_text(row["tmdb_cast"]),
            _list_to_text(row["tmdb_director"]),
            _list_to_text(row["tmdb_director"]),
            _list_to_text(row["tmdb_prod"]),
        ]
        return " ".join(p for p in parts if p).lower().strip()

    joined["tags"] = joined.apply(build_tags, axis=1)

    # 6. Final shape
    movies = joined[["movie_id", "title", "year", "tags"]].copy()
    # Add the original genres column back for display
    movies["genres"] = ml.movies.set_index("movie_id")["genres"].reindex(
        movies["movie_id"]
    ).reset_index(drop=True)
    # Drop movies with no tags at all (rare, but possible)
    movies = movies[movies["tags"].str.len() > 0].reset_index(drop=True)

    n_matched = int(joined["tmdbId"].notna().sum())
    print(
        f"[enriched] {len(movies)} movies, "
        f"{n_matched} matched to TMDB ({n_matched / max(1, len(joined)) * 100:.0f}%)"
    )

    return EnrichedDataset(ratings=ml.ratings, movies=movies)
