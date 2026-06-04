"""HTTP routes for the CINEIQ API."""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Query

from cineiq import __version__
from cineiq.api.schemas import (
    FeatureWeight,
    HealthResponse,
    LimeExplainResponse,
    LimeTermWeight,
    MovieMeta,
    PersonalItem,
    PersonalResponse,
    QueryMeta,
    Recommendation,
    RecommendResponse,
    SearchResponse,
    SignalBreakdown,
    TasteProfileResponse,
)
from cineiq.api.service import service
from cineiq.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    ds = service.dataset
    return HealthResponse(
        status="ok",
        version=__version__,
        dataset=settings.dataset.variant,
        n_movies=(ds.n_movies if ds else 0),
        n_ratings=(ds.n_ratings if ds else 0),
        fitted=service.is_ready,
        personal_ready=service.personal_ready,
    )


@router.get("/search", response_model=SearchResponse, tags=["catalog"])
def search(
    q: str = Query(..., min_length=1, description="Substring of a movie title"),
    limit: int = Query(10, ge=1, le=50),
) -> SearchResponse:
    if not service.is_ready:
        raise HTTPException(503, "service is still warming up")
    df = service.search(q, limit=limit)
    results = [
        MovieMeta(
            movie_id=int(r.movie_id),
            title=str(r.title),
            year=(int(r.year) if r.year is not None and not _isnan(r.year) else None),
            genres=str(r.genres),
        )
        for r in df.itertuples()
    ]
    return SearchResponse(results=results)


@router.get("/recommend", response_model=RecommendResponse, tags=["recommend"])
def recommend(
    title: str | None = Query(None, description="Exact movie title (case-insensitive)"),
    movie_id: int | None = Query(None, description="Internal movie_id, alternative to title"),
    top_n: int = Query(10, ge=1, le=50),
) -> RecommendResponse:
    if not service.is_ready:
        raise HTTPException(503, "service is still warming up")
    if not title and movie_id is None:
        raise HTTPException(422, "Provide either ?title= or ?movie_id=")

    result = (
        service.recommend_by_id(movie_id, top_n=top_n)
        if movie_id is not None
        else service.recommend_by_title(title, top_n=top_n)
    )
    if result is None:
        raise HTTPException(404, f"Title not found in {settings.dataset.variant}")

    return _to_response(result, query=(title or str(movie_id)))


@router.get("/similar", response_model=RecommendResponse, tags=["recommend"])
def similar(
    movie_id: int = Query(..., description="Seed movie_id"),
    top_n: int = Query(10, ge=1, le=50),
) -> RecommendResponse:
    """Alias of /recommend?movie_id=...; kept distinct because the spec names both."""
    if not service.is_ready:
        raise HTTPException(503, "service is still warming up")
    result = service.recommend_by_id(movie_id, top_n=top_n)
    if result is None:
        raise HTTPException(404, "movie_id not found")
    return _to_response(result, query=str(movie_id))


# ---------------------------------------------------------------------------
# Personal (user-level) endpoints — require TMDB data to be loaded
# ---------------------------------------------------------------------------

@router.get(
    "/recommend/user/{user_id}",
    response_model=PersonalResponse,
    tags=["personal"],
)
def recommend_user(
    user_id: int,
    top_n: int = Query(10, ge=1, le=50),
    strategy: str = Query("content", pattern="^(content|collab|hybrid)$"),
) -> PersonalResponse:
    """Personalized recommendations for a known user.

    Available only when TMDB data has been downloaded. Strategies:
      - content : TF-IDF taste centroid (richer than item-item content)
      - collab  : NMF rating prediction
      - hybrid  : blend of both
    """
    if not service.is_ready:
        raise HTTPException(503, "service is still warming up")
    if not service.personal_ready:
        raise HTTPException(
            503,
            "personal models unavailable. Run `python -m cineiq.data.download_tmdb` "
            "and restart the service.",
        )

    result = service.recommend_for_user(user_id, top_n=top_n, strategy=strategy)
    if result is None:
        raise HTTPException(404, f"user_id {user_id} not in training data")
    return PersonalResponse(
        user_id=result["user_id"],
        strategy=result["strategy"],
        latency_ms=result["latency_ms"],
        results=[PersonalItem(**r) for r in result["results"]],
    )


@router.get(
    "/explore/user/{user_id}",
    response_model=TasteProfileResponse,
    tags=["personal"],
)
def explore_user(user_id: int) -> TasteProfileResponse:
    """Get a user's top genres, cast, directors, etc. — their 'taste profile'."""
    if not service.is_ready:
        raise HTTPException(503, "service is still warming up")
    if not service.personal_ready:
        raise HTTPException(503, "personal models unavailable (TMDB not loaded)")

    profile = service.taste_profile_for(user_id)
    if profile is None:
        raise HTTPException(404, f"no taste profile for user_id {user_id}")

    def as_features(pairs: list) -> list[FeatureWeight]:
        return [FeatureWeight(name=n, weight=w) for n, w in pairs]

    return TasteProfileResponse(
        user_id=profile["user_id"],
        top_genres=as_features(profile["top_genres"]),
        top_keywords=as_features(profile["top_keywords"]),
        top_cast=as_features(profile["top_cast"]),
        top_directors=as_features(profile["top_directors"]),
        top_production=as_features(profile["top_production"]),
    )


# ---------------------------------------------------------------------------
# LIME explanation endpoint
# ---------------------------------------------------------------------------

@router.get("/explain/lime", response_model=LimeExplainResponse, tags=["explain"])
def lime_explain(
    seed_id: int = Query(..., description="Seed movie_id"),
    candidate_id: int = Query(..., description="Candidate movie_id to explain"),
    num_features: int = Query(8, ge=1, le=20, description="Number of top terms to return"),
    num_samples: int = Query(1000, ge=100, le=5000, description="LIME perturbation samples (higher = slower but more accurate)"),
) -> LimeExplainResponse:
    """LIME attribution for a seed→candidate pair.

    Returns the content-model terms that most influenced the recommendation score.
    More expensive than /recommend — expect 1-5s response time.
    """
    if not service.is_ready:
        raise HTTPException(503, "service is still warming up")
    t0 = time.perf_counter()
    try:
        attribution = service.lime_explain(seed_id, candidate_id, num_features, num_samples)
    except (KeyError, RuntimeError) as e:
        raise HTTPException(404, str(e))
    latency_ms = int((time.perf_counter() - t0) * 1000)
    return LimeExplainResponse(
        seed_id=attribution.seed_id,
        candidate_id=attribution.candidate_id,
        terms=[LimeTermWeight(term=t, weight=w) for t, w in attribution.terms],
        latency_ms=latency_ms,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _isnan(v) -> bool:
    try:
        return v != v  # NaN != NaN
    except Exception:
        return False


def _to_response(result, *, query: str) -> RecommendResponse:
    recs = [
        Recommendation(
            movie_id=r["movie_id"],
            title=r["title"],
            year=r["year"],
            score=min(1.0, max(0.0, float(r["score"]))),
            score_pct=int(min(99, max(1, round(r["score"] * 100)))),
            reason=r["reason"],
            signals=SignalBreakdown(
                content=r["signals"].get("content"),
                collaborative=r["signals"].get("collaborative"),
                matrix=r["signals"].get("matrix"),
                sentiment=r["signals"].get("sentiment"),
            ),
        )
        for r in result.recommendations
    ]
    return RecommendResponse(
        meta=QueryMeta(
            query=query,
            movie_id=result.seed_id,
            genres=result.seed_genres,
            year=result.seed_year,
            model="hybrid+sentiment",
            latency_ms=result.latency_ms,
        ),
        results=recs,
    )
