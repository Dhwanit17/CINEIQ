"""Tests for sentiment and explainability."""
from __future__ import annotations

from cineiq.models.content import ContentModel
from cineiq.models.hybrid import Candidate, HybridEngine
from cineiq.explain.templates import explain
from cineiq.sentiment.vader import VaderAnalyzer
from cineiq.sentiment.reranker import SentimentReRanker


def test_vader_score_bounds():
    v = VaderAnalyzer()
    pos = v.score("Absolutely brilliant. I loved every second.")
    neg = v.score("Awful. A complete waste of time.")
    neu = v.score("")
    assert pos > 0.5
    assert neg < -0.5
    assert neu == 0.0
    assert -1.0 <= pos <= 1.0 and -1.0 <= neg <= 1.0


def test_reranker_is_noop_without_cache(tiny_dataset):
    rr = SentimentReRanker()
    candidates = HybridEngine().fit(tiny_dataset).similar_to(1, top_n=3)
    reranked = rr.rerank(candidates)
    # No reviews loaded => sentiment dict is empty => order unchanged
    assert [c.movie_id for c in reranked] == [c.movie_id for c in candidates]


def test_reranker_shifts_with_sentiment(tiny_dataset):
    rr = SentimentReRanker()
    candidates = HybridEngine().fit(tiny_dataset).similar_to(1, top_n=5)
    # Inject reviews so the second candidate becomes the most positive
    fake_reviews = {
        candidates[1].movie_id: ["A masterpiece. Beautifully crafted. Brilliant in every way."] * 3,
    }
    rr.warm_cache(fake_reviews)
    reranked = rr.rerank(candidates)
    # The positively-reviewed candidate should now be in the top 2
    top_ids = [c.movie_id for c in reranked[:2]]
    assert candidates[1].movie_id in top_ids


def test_explanation_reason_nonempty(tiny_dataset):
    eng = HybridEngine().fit(tiny_dataset)
    cands = eng.similar_to(1, top_n=1)
    assert cands
    titles = dict(zip(tiny_dataset.movies["movie_id"].astype(int),
                      tiny_dataset.movies["title"].astype(str)))
    ex = explain(seed_id=1, candidate=cands[0],
                 content_model=eng.content, title_lookup=titles)
    assert ex.reason
    assert isinstance(ex.signals, dict)


def test_explanation_handles_lone_candidate():
    # Synthesize a Candidate from a single-signal scenario
    c = Candidate(movie_id=42, score=0.7, components={"matrix": 0.7})
    # Build a minimal content model so the function doesn't blow up
    ex = explain(seed_id=1, candidate=c, content_model=None,  # type: ignore[arg-type]
                 title_lookup={1: "A", 42: "B"})
    assert "latent taste" in ex.reason.lower()
