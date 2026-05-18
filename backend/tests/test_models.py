"""Tests for the recommendation models."""
from __future__ import annotations

import pytest

from cineiq.models.content import ContentModel
from cineiq.models.matrix import MatrixModel
from cineiq.models.hybrid import HybridEngine


def test_content_model_recommends_same_cluster(tiny_dataset):
    m = ContentModel().fit(tiny_dataset)
    # Seed: a sci-fi title
    sims = m.similar_to(1, top_n=5)
    assert sims, "Content model returned no neighbors"
    # All top neighbors should be sci-fi (movie_id < 100)
    for mid in sims:
        assert mid < 100, f"Cross-genre leak: id {mid} from comedy cluster"


def test_content_model_scores_in_unit_interval(tiny_dataset):
    m = ContentModel().fit(tiny_dataset)
    sims = m.similar_to(1, top_n=10)
    for score in sims.values():
        assert 0.0 <= score <= 1.0


def test_matrix_model_returns_neighbors(tiny_dataset):
    m = MatrixModel(n_components=8).fit(tiny_dataset)
    sims = m.similar_to(1, top_n=5)
    assert sims
    assert all(0.0 <= s <= 1.0 for s in sims.values())


def test_hybrid_engine_fuses_components(tiny_dataset):
    eng = HybridEngine().fit(tiny_dataset)
    candidates = eng.similar_to(1, top_n=5)
    assert candidates
    # At least one candidate should have multiple non-empty components
    multi = [c for c in candidates if len(c.components) >= 2]
    assert multi, "No fused candidates — ensemble degraded to single model"


def test_unknown_seed_returns_empty(tiny_dataset):
    m = ContentModel().fit(tiny_dataset)
    assert m.similar_to(99999) == {}
