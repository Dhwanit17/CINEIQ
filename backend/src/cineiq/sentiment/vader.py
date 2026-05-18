"""
VADER sentiment.

Lexicon + rule based. Trained on social media but works surprisingly
well on review text. Returns the compound score, which is the
[-1, 1] normalized sum of valence-weighted lexicon hits.

Cost: zero training, zero memory, microseconds per text. The
default backend until/unless you swap in DistilBERT.
"""
from __future__ import annotations

from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class VaderAnalyzer:
    name = "vader"

    def __init__(self) -> None:
        self._sia = SentimentIntensityAnalyzer()

    @lru_cache(maxsize=10_000)
    def score(self, text: str) -> float:
        if not text:
            return 0.0
        return float(self._sia.polarity_scores(text)["compound"])

    def aggregate(self, texts: list[str]) -> float:
        if not texts:
            return 0.0
        scores = [self.score(t) for t in texts if t]
        return sum(scores) / len(scores) if scores else 0.0
