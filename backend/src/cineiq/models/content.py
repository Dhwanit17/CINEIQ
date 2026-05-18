"""
Content-based recommender: TF-IDF over each movie's content_text,
cosine similarity for neighbors.

This is the cheapest model to train (seconds on 100K) and the most
explainable — we can point at overlapping terms.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from cineiq.data.loader import Dataset
from cineiq.models.base import ScoreMap, normalize_scores


class ContentModel:
    """TF-IDF + cosine similarity over movie content text."""

    name = "content"

    def __init__(self, max_features: int = 5000, ngram_range: tuple[int, int] = (1, 2)) -> None:
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            stop_words="english",
        )
        self.matrix = None              # sparse TF-IDF matrix
        self.movie_ids: np.ndarray | None = None
        self._id_to_row: dict[int, int] = {}
        # Cache feature names so the explainer can name overlapping terms.
        self.feature_names: np.ndarray | None = None

    def fit(self, dataset: Dataset) -> "ContentModel":
        movies = dataset.movies.reset_index(drop=True)
        self.matrix = self.vectorizer.fit_transform(movies["content_text"].fillna(""))
        self.movie_ids = movies["movie_id"].to_numpy()
        self._id_to_row = {int(mid): i for i, mid in enumerate(self.movie_ids)}
        self.feature_names = self.vectorizer.get_feature_names_out()
        return self

    def similar_to(self, movie_id: int, top_n: int = 200) -> ScoreMap:
        if self.matrix is None or movie_id not in self._id_to_row:
            return {}
        row_idx = self._id_to_row[movie_id]
        # linear_kernel == cosine for L2-normalized TF-IDF (sklearn normalizes by default)
        sims = linear_kernel(self.matrix[row_idx], self.matrix).ravel()
        sims[row_idx] = -np.inf  # exclude self
        top = np.argpartition(-sims, min(top_n, len(sims) - 1))[:top_n]
        # Sort the partial result so the highest scores come first
        top = top[np.argsort(-sims[top])]
        result = {
            int(self.movie_ids[i]): float(sims[i])
            for i in top
            if np.isfinite(sims[i]) and sims[i] > 0
        }
        return normalize_scores(result)

    # --- Used by the explainer to name overlapping terms ---
    def shared_terms(self, a: int, b: int, k: int = 5) -> list[str]:
        if self.matrix is None or self.feature_names is None:
            return []
        if a not in self._id_to_row or b not in self._id_to_row:
            return []
        va = self.matrix[self._id_to_row[a]].toarray().ravel()
        vb = self.matrix[self._id_to_row[b]].toarray().ravel()
        contrib = va * vb
        if not np.any(contrib):
            return []
        top = np.argsort(-contrib)[:k]
        return [str(self.feature_names[i]) for i in top if contrib[i] > 0]
