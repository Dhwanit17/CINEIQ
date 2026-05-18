"""
Matrix factorization with scikit-learn's TruncatedSVD on the
user-item ratings matrix.

This is a coarser, faster, sparser cousin of the Surprise SVD —
they often disagree on the long tail, which is what makes the
ensemble useful.
"""
from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from cineiq.data.loader import Dataset
from cineiq.models.base import ScoreMap, normalize_scores


class MatrixModel:
    """TruncatedSVD on the (user x movie) sparse rating matrix."""

    name = "matrix"

    def __init__(self, n_components: int = 50, random_state: int = 42) -> None:
        self.n_components = n_components
        self.random_state = random_state
        self.item_factors: np.ndarray | None = None
        self.movie_ids: np.ndarray | None = None
        self._id_to_row: dict[int, int] = {}

    def fit(self, dataset: Dataset) -> "MatrixModel":
        ratings = dataset.ratings

        # Build a stable movie_id <-> column index mapping.
        movie_ids = np.sort(ratings["movie_id"].unique())
        movie_to_col = {int(mid): c for c, mid in enumerate(movie_ids)}

        user_ids = np.sort(ratings["user_id"].unique())
        user_to_row = {int(uid): r for r, uid in enumerate(user_ids)}

        rows = ratings["user_id"].map(user_to_row).to_numpy()
        cols = ratings["movie_id"].map(movie_to_col).to_numpy()
        vals = ratings["rating"].astype(np.float32).to_numpy()

        mat = csr_matrix(
            (vals, (rows, cols)),
            shape=(len(user_ids), len(movie_ids)),
        )

        # We want item factors, so we decompose the transpose:
        #   mat.T  =  (movies x users)  ->  U_items * Σ * V_users^T
        # TruncatedSVD gives us U·Σ as `fit_transform` output.
        # Clamp n_components so we never exceed the feature dimension
        # (n_users when decomposing the transpose). This matters on tiny
        # datasets and would otherwise crash with a confusing error.
        n_components = min(self.n_components, mat.T.shape[1] - 1)
        n_components = max(2, n_components)
        svd = TruncatedSVD(n_components=n_components, random_state=self.random_state)
        item_factors = svd.fit_transform(mat.T)
        self.item_factors = normalize(item_factors, norm="l2", axis=1)
        self.movie_ids = movie_ids.astype(int)
        self._id_to_row = {int(mid): i for i, mid in enumerate(self.movie_ids)}
        return self

    def similar_to(self, movie_id: int, top_n: int = 200) -> ScoreMap:
        if self.item_factors is None or movie_id not in self._id_to_row:
            return {}
        row_idx = self._id_to_row[movie_id]
        sims = self.item_factors @ self.item_factors[row_idx]
        sims[row_idx] = -np.inf
        top = np.argpartition(-sims, min(top_n, len(sims) - 1))[:top_n]
        top = top[np.argsort(-sims[top])]
        result = {
            int(self.movie_ids[i]): float(sims[i])
            for i in top
            if np.isfinite(sims[i]) and sims[i] > 0
        }
        return normalize_scores(result)
