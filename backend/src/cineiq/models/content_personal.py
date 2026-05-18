"""
Personal content-based recommender (user-level).

Ported from the Content_Based_Recommendations notebook with these
improvements:

  - No hardcoded 500K sample. The full ratings frame flows through.
  - Configurable `liked_threshold` and `max_liked`.
  - Uses cached arrays instead of pandas .iloc loops in hot paths.
  - Exposes BOTH user-level (`recommend_for_user`) AND movie-level
    (`similar_to`) so the hybrid item-item engine could optionally
    consume this richer content signal too.

Strategy: average TF-IDF vectors of the user's liked movies, weighted
by how much they liked each one. Recommend movies most similar to
that centroid.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, vstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from cineiq.data.enriched import EnrichedDataset


@dataclass
class PersonalRecommendation:
    """One row of a personal recommendation list."""
    movie_id: int
    title: str
    score: float


class PersonalContentModel:
    """Builds per-user taste vectors from the TMDB-enriched tag space."""

    name = "personal_content"

    def __init__(
        self,
        max_features: int = 20000,
        ngram_range: tuple[int, int] = (1, 1),
        liked_threshold: float = 4.0,
        max_liked: int = 50,
    ) -> None:
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            stop_words="english",
        )
        self.liked_threshold = liked_threshold
        self.max_liked = max_liked

        # Filled during fit()
        self.matrix: csr_matrix | None = None     # (n_movies, n_features) L2-norm
        self.movie_ids: np.ndarray | None = None
        self._id_to_row: dict[int, int] = {}
        self.titles: dict[int, str] = {}
        # User -> (sparse row vector, set of seen movie_ids)
        self._user_vectors: dict[int, csr_matrix] = {}
        self._user_seen: dict[int, set[int]] = {}

    def fit(self, dataset: EnrichedDataset) -> "PersonalContentModel":
        movies = dataset.movies.reset_index(drop=True)
        # Fit + L2-normalize so cosine == dot product
        matrix = self.vectorizer.fit_transform(movies["tags"].fillna(""))
        self.matrix = normalize(matrix, norm="l2", axis=1, copy=False)
        self.movie_ids = movies["movie_id"].to_numpy(dtype=np.int64)
        self._id_to_row = {int(mid): i for i, mid in enumerate(self.movie_ids)}
        self.titles = dict(zip(movies["movie_id"].astype(int), movies["title"].astype(str)))

        self._build_user_vectors(dataset.ratings)
        return self

    def _build_user_vectors(self, ratings: pd.DataFrame) -> None:
        """Compute one centroid TF-IDF vector per user and cache it."""
        assert self.matrix is not None
        liked = ratings[ratings["rating"] >= self.liked_threshold]
        # Keep only ratings on movies we have content vectors for
        liked = liked[liked["movie_id"].isin(self._id_to_row.keys())]

        # Track everything seen (rated, not just liked) so we can exclude later
        for uid, group in ratings.groupby("user_id"):
            self._user_seen[int(uid)] = set(group["movie_id"].astype(int))

        # Build a centroid per user
        for uid, group in liked.groupby("user_id"):
            # Cap to top-N highest-rated to keep centroids focused
            top = group.sort_values("rating", ascending=False).head(self.max_liked)
            # Weights: rating 4.0 -> 1.0, 4.5 -> 1.5, 5.0 -> 2.0
            weights = (top["rating"].to_numpy() - self.liked_threshold + 1.0)
            rows = np.array(
                [self._id_to_row[int(mid)] for mid in top["movie_id"]],
                dtype=np.int64,
            )
            liked_vecs = self.matrix[rows]
            # Weighted average. The weighted sum keeps the result sparse;
            # we re-normalize so it's a unit vector in the same space.
            weighted = liked_vecs.multiply(weights.reshape(-1, 1))
            centroid = csr_matrix(weighted.sum(axis=0) / weights.sum())
            centroid = normalize(centroid, norm="l2", axis=1, copy=False)
            self._user_vectors[int(uid)] = centroid

    # ----- queries -----

    def has_user(self, user_id: int) -> bool:
        return user_id in self._user_vectors

    def recommend_for_user(
        self,
        user_id: int,
        top_n: int = 10,
        exclude_seen: bool = True,
        min_score: float = 0.01,
    ) -> list[PersonalRecommendation]:
        """Top-N recommendations for a user using the cached centroid."""
        if self.matrix is None or user_id not in self._user_vectors:
            return []
        user_vec = self._user_vectors[user_id]
        scores = (self.matrix @ user_vec.T).toarray().ravel()

        if exclude_seen:
            seen = self._user_seen.get(user_id, set())
            for mid in seen:
                idx = self._id_to_row.get(int(mid))
                if idx is not None:
                    scores[idx] = -np.inf

        # Filter + sort
        mask = np.isfinite(scores) & (scores >= min_score)
        candidate_idx = np.where(mask)[0]
        if not candidate_idx.size:
            return []
        order = candidate_idx[np.argsort(-scores[candidate_idx])][:top_n]
        return [
            PersonalRecommendation(
                movie_id=int(self.movie_ids[i]),
                title=self.titles.get(int(self.movie_ids[i]), ""),
                score=float(scores[i]),
            )
            for i in order
        ]

    def similar_to(self, movie_id: int, top_n: int = 200) -> dict[int, float]:
        """Movie-to-movie similarity (so this model can also feed the hybrid)."""
        if self.matrix is None or movie_id not in self._id_to_row:
            return {}
        row_idx = self._id_to_row[movie_id]
        seed = self.matrix[row_idx]
        sims = (self.matrix @ seed.T).toarray().ravel()
        sims[row_idx] = -np.inf
        top = np.argpartition(-sims, min(top_n, len(sims) - 1))[:top_n]
        top = top[np.argsort(-sims[top])]
        return {
            int(self.movie_ids[i]): float(sims[i])
            for i in top
            if np.isfinite(sims[i]) and sims[i] > 0
        }
