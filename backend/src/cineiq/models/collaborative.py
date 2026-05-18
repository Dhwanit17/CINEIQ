"""
Collaborative filtering via Non-negative Matrix Factorization (NMF).

Originally we used scikit-surprise's SVD here, but that library is
unmaintained and frequently fails to install on modern Python/Windows.
We've replaced it with scikit-learn's NMF, which:

  - is pure-Python wrapping scipy — ships wheels for every platform
  - learns *non-negative* latent factors, which is qualitatively
    different from TruncatedSVD in MatrixModel. NMF factors are
    additive "taste components" (one might be "loves dark sci-fi",
    another "loves family animation"), while TruncatedSVD factors
    can cancel each other out. The ensemble is stronger when its
    sub-models disagree, so this is actually a good thing.

Both produce L2-normalized item factors and use cosine similarity
for neighbors. Same `similar_to()` contract as every other model.
"""
from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import NMF
from sklearn.preprocessing import normalize

from cineiq.data.loader import Dataset
from cineiq.models.base import ScoreMap, normalize_scores


class CollaborativeModel:
    """Item-item neighbors derived from NMF item factors over user-item ratings."""

    name = "collaborative"

    def __init__(
        self,
        n_components: int = 30,
        max_iter: int = 200,
        random_state: int = 42,
    ) -> None:
        self.n_components = n_components
        self.max_iter = max_iter
        self.random_state = random_state
        self.item_factors: np.ndarray | None = None
        self.movie_ids: np.ndarray | None = None
        self._id_to_row: dict[int, int] = {}

    def fit(self, dataset: Dataset) -> "CollaborativeModel":
        ratings = dataset.ratings

        # Stable id ↔ index mappings
        movie_ids = np.sort(ratings["movie_id"].unique())
        movie_to_col = {int(mid): c for c, mid in enumerate(movie_ids)}
        user_ids = np.sort(ratings["user_id"].unique())
        user_to_row = {int(uid): r for r, uid in enumerate(user_ids)}

        rows = ratings["user_id"].map(user_to_row).to_numpy()
        cols = ratings["movie_id"].map(movie_to_col).to_numpy()
        # NMF requires non-negative inputs. Movie ratings are already 1–5,
        # so we're good — no shift needed.
        vals = ratings["rating"].astype(np.float32).to_numpy()

        mat = csr_matrix(
            (vals, (rows, cols)),
            shape=(len(user_ids), len(movie_ids)),
        )

        # Clamp n_components for tiny datasets (tests use ~30 movies)
        n_components = min(self.n_components, min(mat.shape) - 1)
        n_components = max(2, n_components)

        # NMF on (users x movies). The components_ attribute gives us
        # (n_components, n_movies) — each column is a movie's latent vector.
        model = NMF(
            n_components=n_components,
            max_iter=self.max_iter,
            random_state=self.random_state,
            init="nndsvd",          # deterministic, faster convergence
            tol=1e-4,
        )
        # We don't actually need the user factors (model.fit_transform),
        # just the item factors (model.components_). Calling .fit() avoids
        # holding the user matrix in memory.
        model.fit(mat)
        # Transpose so each row is a movie's factor vector
        factors = model.components_.T  # shape (n_movies, n_components)

        self.item_factors = normalize(factors, norm="l2", axis=1)
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
