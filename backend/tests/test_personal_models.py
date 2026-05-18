"""Tests for the personal (user-level) models ported from the notebooks."""
from __future__ import annotations

import pandas as pd
import pytest

from cineiq.data.enriched import EnrichedDataset
from cineiq.models.content_personal import PersonalContentModel
from cineiq.models.collaborative_personal import PersonalCollaborativeModel


@pytest.fixture(scope="session")
def enriched_dataset(tiny_dataset) -> EnrichedDataset:
    """Wrap the tiny synthetic dataset in EnrichedDataset shape.

    The personal_content model takes `EnrichedDataset` which has `tags`
    instead of `content_text`. We synthesize tags by reusing
    content_text — same idea, different column name.
    """
    movies = tiny_dataset.movies.copy()
    movies["tags"] = movies["content_text"]
    return EnrichedDataset(ratings=tiny_dataset.ratings, movies=movies)


def test_personal_content_recommends_for_known_user(enriched_dataset):
    m = PersonalContentModel().fit(enriched_dataset)
    # User 1 in the tiny fixture is a sci-fi lover (movie_ids 1-15)
    recs = m.recommend_for_user(1, top_n=5)
    assert len(recs) > 0
    # Should mostly recommend other sci-fi titles (id < 100)
    scifi_hits = sum(1 for r in recs if r.movie_id < 100)
    assert scifi_hits >= 3, f"Expected >=3 sci-fi recs, got {scifi_hits}"


def test_personal_content_excludes_seen(enriched_dataset):
    m = PersonalContentModel().fit(enriched_dataset)
    user_id = 1
    seen = set(enriched_dataset.ratings[
        enriched_dataset.ratings["user_id"] == user_id
    ]["movie_id"])
    recs = m.recommend_for_user(user_id, top_n=10, exclude_seen=True)
    rec_ids = {r.movie_id for r in recs}
    assert not (rec_ids & seen), "Returned a movie the user has already rated"


def test_personal_content_unknown_user(enriched_dataset):
    m = PersonalContentModel().fit(enriched_dataset)
    assert m.recommend_for_user(99999) == []


def test_personal_content_supports_movie_similarity(enriched_dataset):
    m = PersonalContentModel().fit(enriched_dataset)
    sims = m.similar_to(1, top_n=5)
    assert sims
    assert all(0.0 <= s for s in sims.values())


def test_personal_collab_predicts_ratings(tiny_dataset):
    m = PersonalCollaborativeModel(min_rating_count=2).fit(tiny_dataset)
    recs = m.recommend_for_user(1, top_n=5)
    assert recs
    for r in recs:
        # Predictions should be in the original rating range (1-5)
        assert tiny_dataset.ratings["rating"].min() <= r.pred_rating <= tiny_dataset.ratings["rating"].max() + 0.01
        assert r.rating_count >= 2


def test_personal_collab_unknown_user(tiny_dataset):
    m = PersonalCollaborativeModel().fit(tiny_dataset)
    assert m.recommend_for_user(99999) == []


def test_personal_collab_respects_min_rating_count(tiny_dataset):
    """If min_rating_count is set very high, fewer/no candidates pass the filter."""
    strict = PersonalCollaborativeModel(min_rating_count=100).fit(tiny_dataset)
    lenient = PersonalCollaborativeModel(min_rating_count=1).fit(tiny_dataset)
    assert len(strict.recommend_for_user(1, top_n=10)) <= len(lenient.recommend_for_user(1, top_n=10))
