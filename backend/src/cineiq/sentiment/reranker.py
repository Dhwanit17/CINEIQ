"""
Sentiment-aware re-ranker.

Given hybrid candidates and a corpus of reviews keyed by movie_id,
nudges each candidate's score by its sentiment delta. The shift is
bounded by `influence` from config so a single hot-take review
can't catapult an otherwise weak match.

Until we wire up real IMDB reviews, we can pass an empty review
corpus and this reduces to a no-op — the hybrid ordering is preserved.
"""
from __future__ import annotations

from cineiq.config import SentimentConfig, settings
from cineiq.models.hybrid import Candidate
from cineiq.sentiment.base import SentimentAnalyzer, make_analyzer


class SentimentReRanker:
    def __init__(
        self,
        analyzer: SentimentAnalyzer | None = None,
        config: SentimentConfig | None = None,
    ) -> None:
        cfg = config or settings.sentiment
        self.config = cfg
        self.analyzer = analyzer or make_analyzer(cfg.backend)
        # Cache: movie_id -> aggregated sentiment in [-1, 1]
        self._cache: dict[int, float] = {}

    def warm_cache(self, reviews_by_movie: dict[int, list[str]]) -> None:
        """Pre-compute sentiment per movie so re-ranking is O(N) at request time."""
        for mid, texts in reviews_by_movie.items():
            self._cache[mid] = self.analyzer.aggregate(texts)

    def sentiment_for(self, movie_id: int) -> float:
        return self._cache.get(movie_id, 0.0)

    def rerank(self, candidates: list[Candidate]) -> list[Candidate]:
        if not self.config.enabled or not self._cache:
            return candidates

        influence = self.config.influence
        rescored = []
        for c in candidates:
            sent = self.sentiment_for(c.movie_id)
            # Map sentiment from [-1, 1] to a multiplier in [1-inf, 1+inf]
            new_score = c.score * (1.0 + influence * sent)
            rescored.append(
                Candidate(
                    movie_id=c.movie_id,
                    score=new_score,
                    components={**c.components, "sentiment": sent},
                )
            )
        rescored.sort(key=lambda x: x.score, reverse=True)
        return rescored
