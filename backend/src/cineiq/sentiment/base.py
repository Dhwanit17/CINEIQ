"""Sentiment analyzers with a uniform interface."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SentimentAnalyzer(Protocol):
    """Returns a sentiment score in [-1, 1] for a body of text."""

    name: str

    def score(self, text: str) -> float:
        ...

    def aggregate(self, texts: list[str]) -> float:
        """Aggregate sentiment over many texts (e.g. all reviews for a movie)."""
        ...


def make_analyzer(backend: str) -> SentimentAnalyzer:
    """Factory that returns the configured backend."""
    if backend == "vader":
        from cineiq.sentiment.vader import VaderAnalyzer
        return VaderAnalyzer()
    if backend == "distilbert":
        from cineiq.sentiment.distilbert import DistilBertAnalyzer
        return DistilBertAnalyzer()
    raise ValueError(f"Unknown sentiment backend: {backend!r}")
