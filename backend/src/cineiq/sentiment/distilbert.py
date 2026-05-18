"""
DistilBERT sentiment — STUB.

The interface is real and the API will accept `model=distilbert`. Wiring
the model up is intentionally left for when you have GPU access or are
ready to depend on torch. To enable:

    1. pip install torch transformers
    2. Replace the body of `score()` below with:

        from transformers import pipeline
        self._pipe = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
        )
        out = self._pipe(text[:512])[0]
        sign = 1.0 if out["label"] == "POSITIVE" else -1.0
        return sign * float(out["score"])

    3. Initialize the pipeline once in __init__, not per-call.
"""
from __future__ import annotations


class DistilBertAnalyzer:
    name = "distilbert"

    def __init__(self) -> None:
        raise NotImplementedError(
            "DistilBERT backend is a stub. See cineiq/sentiment/distilbert.py "
            "for the 5-line activation recipe."
        )

    def score(self, text: str) -> float:  # pragma: no cover
        raise NotImplementedError

    def aggregate(self, texts: list[str]) -> float:  # pragma: no cover
        raise NotImplementedError
