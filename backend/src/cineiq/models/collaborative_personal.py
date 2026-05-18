"""
Personal collaborative filtering (user-level).

Ports the *strategy* of the Collaborative_Filtering notebook (predict a
rating for every unseen movie, sort by predicted rating, return top-N)
but uses the NMF factorization we already have in `CollaborativeModel`
instead of scikit-surprise. That keeps us off the broken Surprise
install path on Windows.

The notebook used `min_rating_count` as a confidence filter so the model
doesn't recommend obscurities with three ratings from three friends.
We carry that filter forward — it's a genuinely good idea.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import NMF
from sklearn.preprocessing import normalize

from cineiq.data.loader import Dataset


@dataclass
class PersonalRecommendation:
    movie_id: int
    title: str
    pred_rating: float
    avg_rating: float
    rating_count: int


class PersonalCollaborativeModel:
    """
    Predict user-movie rating via NMF factors, then rank unseen movies.

    Decomposes the (users × movies) rating matrix into user factors U
    and item factors V. The predicted rating for (user u, movie m) is
    `dot(U[u], V[m])`, then rescaled to the original rating scale.
    """

    name = "personal_collab"

    def __init__(
        self,
        n_components: int = 30,
        max_iter: int = 200,
        random_state: int = 42,
        min_rating_count: int = 20,
    ) -> None:
        self.n_components = n_components
        self.max_iter = max_iter
        self.random_state = random_state
        self.min_rating_count = min_rating_count

        # Filled during fit()
        self.user_factors: np.ndarray | None = None
        self.item_factors: np.ndarray | None = None
        self.user_ids: np.ndarray | None = None
        self.movie_ids: np.ndarray | None = None
        self._user_to_row: dict[int, int] = {}
        self._movie_to_col: dict[int, int] = {}

        # Rating scale for sensible-looking output (the page shows things like
        # "pred=4.3" — easier to read than raw factor dot products).
        self._rating_min: float = 0.5
        self._rating_max: float = 5.0
        self._dot_max: float = 1.0   # set during fit

        # Per-movie stats for the confidence filter
        self.movie_stats: pd.DataFrame | None = None
        # Per-user seen sets for exclude_seen
        self._user_seen: dict[int, set[int]] = {}
        self._titles: dict[int, str] = {}

    def fit(self, dataset: Dataset) -> "PersonalCollaborativeModel":
        ratings = dataset.ratings

        # Stable id mappings
        user_ids = np.sort(ratings["user_id"].unique())
        movie_ids = np.sort(ratings["movie_id"].unique())
        self._user_to_row = {int(u): r for r, u in enumerate(user_ids)}
        self._movie_to_col = {int(m): c for c, m in enumerate(movie_ids)}
        self.user_ids = user_ids.astype(np.int64)
        self.movie_ids = movie_ids.astype(np.int64)

        # Build the sparse rating matrix
        rows = ratings["user_id"].map(self._user_to_row).to_numpy()
        cols = ratings["movie_id"].map(self._movie_to_col).to_numpy()
        vals = ratings["rating"].astype(np.float32).to_numpy()
        self._rating_min = float(ratings["rating"].min())
        self._rating_max = float(ratings["rating"].max())
        mat = csr_matrix(
            (vals, (rows, cols)),
            shape=(len(user_ids), len(movie_ids)),
        )

        # Clamp components for tiny datasets
        n_components = min(self.n_components, min(mat.shape) - 1)
        n_components = max(2, n_components)

        model = NMF(
            n_components=n_components,
            max_iter=self.max_iter,
            random_state=self.random_state,
            init="nndsvd",
            tol=1e-4,
        )
        self.user_factors = model.fit_transform(mat)         # (n_users, k)
        self.item_factors = model.components_.T              # (n_movies, k)

        # Estimate the max plausible dot product so we can rescale to the
        # rating range. Using percentile, not max, avoids one outlier
        # ballooning the scale.
        sample_preds = self.user_factors @ self.item_factors[
            np.random.default_rng(0).choice(len(self.movie_ids), size=min(200, len(self.movie_ids)))
        ].T
        self._dot_max = max(1e-6, float(np.percentile(sample_preds, 99)))

        # Movie-level stats for the confidence filter
        self.movie_stats = (
            ratings.groupby("movie_id")
            .agg(avg_rating=("rating", "mean"), rating_count=("rating", "count"))
            .reset_index()
        )

        # Seen movies per user
        for uid, group in ratings.groupby("user_id"):
            self._user_seen[int(uid)] = set(group["movie_id"].astype(int))

        # Titles for display
        self._titles = dict(
            zip(dataset.movies["movie_id"].astype(int),
                dataset.movies["title"].astype(str))
        )
        return self

    # ----- queries -----

    def has_user(self, user_id: int) -> bool:
        return user_id in self._user_to_row

    def _predict_rating(self, pred_dot: np.ndarray) -> np.ndarray:
        """Rescale raw NMF dot-products to the original rating range."""
        clipped = np.clip(pred_dot, 0.0, self._dot_max)
        return self._rating_min + (clipped / self._dot_max) * (self._rating_max - self._rating_min)

    def recommend_for_user(
        self,
        user_id: int,
        top_n: int = 10,
        exclude_seen: bool = True,
    ) -> list[PersonalRecommendation]:
        if self.user_factors is None or self.item_factors is None:
            return []
        if user_id not in self._user_to_row:
            return []
        assert self.movie_stats is not None

        row = self._user_to_row[user_id]
        raw_scores = self.item_factors @ self.user_factors[row]
        preds = self._predict_rating(raw_scores)

        # Build a DataFrame for filtering / sorting
        df = pd.DataFrame({
            "movie_id": self.movie_ids,
            "pred_rating": preds,
        })

        # Confidence filter
        df = df.merge(self.movie_stats, on="movie_id", how="left")
        df = df[df["rating_count"].fillna(0) >= self.min_rating_count]

        # Exclude seen
        if exclude_seen:
            seen = self._user_seen.get(user_id, set())
            if seen:
                df = df[~df["movie_id"].isin(seen)]

        # Sort: predicted rating first, then average (popularity tiebreaker)
        df = df.sort_values(
            ["pred_rating", "avg_rating", "rating_count"],
            ascending=[False, False, False],
        ).head(top_n)

        return [
            PersonalRecommendation(
                movie_id=int(r.movie_id),
                title=self._titles.get(int(r.movie_id), ""),
                pred_rating=float(r.pred_rating),
                avg_rating=float(r.avg_rating),
                rating_count=int(r.rating_count),
            )
            for r in df.itertuples()
        ]
