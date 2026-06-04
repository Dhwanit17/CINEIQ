"""Pydantic schemas defining the API contract."""
from __future__ import annotations

from pydantic import BaseModel, Field


class MovieMeta(BaseModel):
    movie_id: int
    title: str
    year: int | None = None
    genres: str = ""


class SignalBreakdown(BaseModel):
    """Per-model contribution to a recommendation's score."""

    content: float | None = None
    collaborative: float | None = None
    matrix: float | None = None
    sentiment: float | None = None


class Recommendation(BaseModel):
    movie_id: int
    title: str
    year: int | None = None
    score: float = Field(..., ge=0.0, le=1.0, description="Final hybrid score")
    score_pct: int = Field(..., ge=0, le=100, description="Score as a 0-100 integer for UI")
    reason: str
    signals: SignalBreakdown


class QueryMeta(BaseModel):
    """Metadata about the query itself, mirrored back to the client."""

    query: str
    movie_id: int
    genres: str = ""
    year: int | None = None
    model: str = "hybrid"
    latency_ms: int


class RecommendResponse(BaseModel):
    meta: QueryMeta
    results: list[Recommendation]


class SearchResponse(BaseModel):
    results: list[MovieMeta]


class HealthResponse(BaseModel):
    status: str
    version: str
    dataset: str
    n_movies: int
    n_ratings: int
    fitted: bool
    personal_ready: bool = False


# ---------------------------------------------------------------------------
# Personal (user-level) recommendation schemas
# ---------------------------------------------------------------------------

class PersonalItem(BaseModel):
    movie_id: int
    title: str
    score: float
    source: str
    # Optional fields, only present for collab/hybrid strategies
    pred_rating: float | None = None
    avg_rating: float | None = None
    rating_count: int | None = None
    content_score: float | None = None
    collab_score: float | None = None


class PersonalResponse(BaseModel):
    user_id: int
    strategy: str
    latency_ms: int
    results: list[PersonalItem]


class FeatureWeight(BaseModel):
    name: str
    weight: float


class TasteProfileResponse(BaseModel):
    user_id: int
    top_genres: list[FeatureWeight]
    top_keywords: list[FeatureWeight]
    top_cast: list[FeatureWeight]
    top_directors: list[FeatureWeight]
    top_production: list[FeatureWeight]


class LimeTermWeight(BaseModel):
    term: str
    weight: float


class LimeExplainResponse(BaseModel):
    seed_id: int
    candidate_id: int
    terms: list[LimeTermWeight]
    latency_ms: int
