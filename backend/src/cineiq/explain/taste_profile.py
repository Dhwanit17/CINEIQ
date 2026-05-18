"""
User taste profile extraction.

Given a user's rating history and the enriched (TMDB) dataset, computes
their top genres, keywords, cast, directors, and production companies.
This is what the spec calls the "User Taste Dashboard" — directly
useful for the Streamlit interface and the `/explore/user/{id}` API.

The math is straightforward: for each feature (genre etc.), sum
(rating - threshold + 1) across all of a user's liked films that have
that feature. Return the top K.

Ported from the notebook's `get_top_user_features`, but operating
on parsed lists in memory instead of repeatedly exploding the frame.
"""
from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass

import pandas as pd

from cineiq.config import DATA_DIR


@dataclass
class TasteProfile:
    user_id: int
    top_genres: list[tuple[str, float]]
    top_keywords: list[tuple[str, float]]
    top_cast: list[tuple[str, float]]
    top_directors: list[tuple[str, float]]
    top_production: list[tuple[str, float]]


class TasteProfiler:
    """Builds per-user taste summaries from TMDB-tagged movies."""

    def __init__(self, liked_threshold: float = 4.0, top_k: int = 10) -> None:
        self.liked_threshold = liked_threshold
        self.top_k = top_k
        # Parsed feature lists keyed by movie_id (filled in fit())
        self._features: dict[int, dict[str, list[str]]] = {}

    def fit(self, enriched_movies_path: str | None = None) -> "TasteProfiler":
        """Re-parse TMDB JSON columns into per-movie feature lists.

        We re-read the raw TMDB CSV here rather than relying on the
        EnrichedDataset (which has flattened everything into one tag
        string). The profile breakdown needs the structured lists.
        """
        tmdb_dir = DATA_DIR / "tmdb"
        movies = pd.read_csv(tmdb_dir / "tmdb_5000_movies.csv")
        credits = pd.read_csv(tmdb_dir / "tmdb_5000_credits.csv")

        # Join by tmdbId
        movies["tmdbId"] = movies["id"]
        credits["tmdbId"] = credits["movie_id"]
        tmdb = movies.merge(
            credits[["tmdbId", "cast", "crew"]],
            on="tmdbId",
            how="inner",
        )

        # We need a MovieLens movieId <-> tmdbId mapping to key by movie_id.
        # Use the same normalizer as the enriched loader.
        from cineiq.data.loader import load_dataset
        from cineiq.data.enriched import _normalize_title
        ml = load_dataset()
        ml_movies = ml.movies.copy()
        ml_movies["_title_clean"] = ml_movies["title"].apply(_normalize_title)
        tmdb["_title_clean"] = tmdb["title"].apply(_normalize_title)
        joined = ml_movies.merge(
            tmdb,
            on="_title_clean",
            how="inner",
            suffixes=("_ml", "_tmdb"),
        )

        for r in joined.itertuples(index=False):
            self._features[int(r.movie_id)] = {
                "genres": self._parse_names(r.genres_tmdb if hasattr(r, "genres_tmdb") else r.genres),
                "keywords": self._parse_names(r.keywords),
                "cast": self._parse_names(r.cast, limit=5),
                "directors": self._parse_directors(r.crew),
                "production": self._parse_names(r.production_companies),
            }
        return self

    @staticmethod
    def _parse_obj(x):
        if isinstance(x, list):
            return x
        if pd.isna(x):
            return []
        try:
            return ast.literal_eval(x)
        except (ValueError, SyntaxError, TypeError):
            return []

    @classmethod
    def _parse_names(cls, raw, limit: int | None = None) -> list[str]:
        items = cls._parse_obj(raw)
        out = [d["name"] for d in items if isinstance(d, dict) and "name" in d]
        return out[:limit] if limit else out

    @classmethod
    def _parse_directors(cls, raw) -> list[str]:
        items = cls._parse_obj(raw)
        return [d["name"] for d in items if isinstance(d, dict) and d.get("job") == "Director"]

    def profile(self, user_id: int, ratings: pd.DataFrame) -> TasteProfile:
        liked = ratings[(ratings["user_id"] == user_id) & (ratings["rating"] >= self.liked_threshold)]
        if liked.empty:
            return TasteProfile(user_id, [], [], [], [], [])

        scores: dict[str, Counter] = {k: Counter() for k in ("genres", "keywords", "cast", "directors", "production")}
        for r in liked.itertuples(index=False):
            mid = int(r.movie_id)
            if mid not in self._features:
                continue
            weight = float(r.rating) - self.liked_threshold + 1.0
            for kind, names in self._features[mid].items():
                for name in names:
                    scores[kind][name] += weight

        def top_of(kind: str) -> list[tuple[str, float]]:
            return [(name, float(w)) for name, w in scores[kind].most_common(self.top_k)]

        return TasteProfile(
            user_id=user_id,
            top_genres=top_of("genres"),
            top_keywords=top_of("keywords"),
            top_cast=top_of("cast"),
            top_directors=top_of("directors"),
            top_production=top_of("production"),
        )
