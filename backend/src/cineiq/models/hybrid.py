"""
Hybrid recommendation engine.

Strategy: weighted sum over the union of candidates from each sub-model.
Each sub-model returns its own normalized [0,1] scores; we weight,
add, and rank.

Why weighted-sum and not rank fusion (RRF, Borda)? Because the spec
says "weighted ensemble" and because it's the easiest fusion to
explain to users — and explanation is half the product.
"""
from __future__ import annotations

from dataclasses import dataclass

from cineiq.config import HybridWeights, settings
from cineiq.data.loader import Dataset
from cineiq.models.base import ScoreMap, SimilarityModel
from cineiq.models.collaborative import CollaborativeModel
from cineiq.models.content import ContentModel
from cineiq.models.matrix import MatrixModel


@dataclass
class Candidate:
    movie_id: int
    score: float
    # Per-model contribution for transparency
    components: dict[str, float]


class HybridEngine:
    """Fuses content, collaborative, and matrix-SVD similarities."""

    def __init__(self, weights: HybridWeights | None = None) -> None:
        self.weights = weights or settings.weights
        self.content = ContentModel()
        self.collab = CollaborativeModel()
        self.matrix = MatrixModel()
        self._fitted = False

    @property
    def models(self) -> list[tuple[float, SimilarityModel]]:
        return [
            (self.weights.content, self.content),
            (self.weights.collaborative, self.collab),
            (self.weights.matrix, self.matrix),
        ]

    def fit(self, dataset: Dataset) -> "HybridEngine":
        # Content is fast and always works. Try CF first; if Surprise
        # can't initialize, log it and continue with the other two.
        self.content.fit(dataset)
        try:
            self.collab.fit(dataset)
        except Exception as exc:  # pragma: no cover  (env-specific)
            print(f"[warn] collaborative model unavailable: {exc!r}")
        self.matrix.fit(dataset)
        self._fitted = True
        return self

    def similar_to(self, movie_id: int, top_n: int | None = None) -> list[Candidate]:
        if not self._fitted:
            raise RuntimeError("HybridEngine.fit() must be called before recommending")
        pool = top_n or settings.candidate_pool_size

        fused: dict[int, float] = {}
        components: dict[int, dict[str, float]] = {}

        # Renormalize weights so they sum to 1 regardless of what user passed
        total = sum(w for w, _ in self.models) or 1.0

        for weight, model in self.models:
            if weight <= 0:
                continue
            w = weight / total
            scores: ScoreMap = model.similar_to(movie_id, top_n=pool)
            for mid, s in scores.items():
                fused[mid] = fused.get(mid, 0.0) + w * s
                components.setdefault(mid, {})[model.name] = s

        # Sort, take top, return as Candidate objects
        ordered = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:pool]
        return [
            Candidate(
                movie_id=mid,
                score=score,
                components=components.get(mid, {}),
            )
            for mid, score in ordered
        ]
