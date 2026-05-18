"""
Shared types for recommendation models.

Every sub-model implements the same `similar_to(movie_id)` contract,
returning `{movie_id: score}` where score is in [0, 1]. The hybrid
ensemble fuses these dicts.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

ScoreMap = dict[int, float]


@runtime_checkable
class SimilarityModel(Protocol):
    """A model that can rank movies by similarity to a seed movie."""

    name: str

    def similar_to(self, movie_id: int, top_n: int = 200) -> ScoreMap:
        """Return up to `top_n` movie_ids most similar to the seed, with scores."""
        ...


def normalize_scores(scores: ScoreMap) -> ScoreMap:
    """Min-max normalize a score dict to [0, 1]. Empty dicts pass through."""
    if not scores:
        return scores
    values = list(scores.values())
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return {k: 1.0 for k in scores}
    span = hi - lo
    return {k: (v - lo) / span for k, v in scores.items()}
