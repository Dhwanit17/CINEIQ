"""
Recommendation service with verbose startup diagnostics.

This version logs every step of warm-up and refuses to silently swallow
errors during personal-model fitting.
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass

from cineiq.data.loader import Dataset, load_dataset
from cineiq.explain.templates import explain
from cineiq.models.hybrid import HybridEngine
from cineiq.sentiment.reranker import SentimentReRanker


@dataclass
class RecommendationResult:
    seed_id: int
    seed_title: str
    seed_genres: str
    seed_year: int | None
    recommendations: list
    latency_ms: int


class RecommendationService:
    def __init__(self) -> None:
        print(f"[service.__init__] creating new RecommendationService id={id(self)}")
        self.dataset: Dataset | None = None
        self.engine: HybridEngine | None = None
        self.reranker: SentimentReRanker | None = None
        self._title_lookup: dict[int, str] = {}
        self.personal_content = None
        self.personal_collab = None
        self.taste_profiler = None
        self.personal_ready: bool = False

    @property
    def is_ready(self) -> bool:
        return self.engine is not None and self.engine._fitted

    def warm_up(self) -> None:
        print(f"[service.warm_up] start, service id={id(self)}")
        t0 = time.perf_counter()
        self.dataset = load_dataset()
        self.engine = HybridEngine().fit(self.dataset)
        self.reranker = SentimentReRanker()
        self._title_lookup = dict(
            zip(self.dataset.movies["movie_id"].astype(int),
                self.dataset.movies["title"].astype(str))
        )
        print(f"[service] item-item warm-up done in {time.perf_counter() - t0:.2f}s")

        # Personal model warmup with FULL error visibility
        print("[service] attempting to load personal models...")
        try:
            self._warm_up_personal()
            print(f"[service.warm_up] DONE, personal_ready={self.personal_ready}, id={id(self)}")
        except FileNotFoundError as e:
            print(f"[service] personal models unavailable (missing data): {e}")
            print("[service] run `python -m cineiq.data.download_tmdb` and restart")
        except Exception as e:
            print(f"[service] personal models FAILED: {type(e).__name__}: {e}")
            print("[service] FULL TRACEBACK:")
            traceback.print_exc()
            print("[service] (end of traceback)")

    def _warm_up_personal(self) -> None:
        print("[service._warm_up_personal] importing modules...")
        from cineiq.data.enriched import load_enriched
        from cineiq.models.content_personal import PersonalContentModel
        from cineiq.models.collaborative_personal import PersonalCollaborativeModel
        from cineiq.explain.taste_profile import TasteProfiler

        t0 = time.perf_counter()
        print("[service._warm_up_personal] calling load_enriched()...")
        enriched = load_enriched()
        print(f"[service._warm_up_personal] enriched loaded, {enriched.n_movies} movies")

        print("[service._warm_up_personal] fitting PersonalContentModel...")
        self.personal_content = PersonalContentModel().fit(enriched)
        print("[service._warm_up_personal] PersonalContentModel done")

        print("[service._warm_up_personal] fitting PersonalCollaborativeModel...")
        self.personal_collab = PersonalCollaborativeModel().fit(self.dataset)
        print("[service._warm_up_personal] PersonalCollaborativeModel done")

        print("[service._warm_up_personal] fitting TasteProfiler...")
        self.taste_profiler = TasteProfiler().fit()
        print("[service._warm_up_personal] TasteProfiler done")

        self.personal_ready = True
        print(f"[service] personal models fitted in {time.perf_counter() - t0:.2f}s, personal_ready=True")

    def search(self, query: str, limit: int = 10):
        assert self.dataset is not None
        return self.dataset.search_titles(query, limit=limit)

    def recommend_by_title(self, title: str, top_n: int = 10) -> RecommendationResult | None:
        assert self.dataset is not None
        movie_id = self.dataset.title_to_id(title)
        if movie_id is None:
            return None
        return self.recommend_by_id(movie_id, top_n=top_n)

    def recommend_by_id(self, movie_id: int, top_n: int = 10) -> RecommendationResult | None:
        assert self.dataset is not None and self.engine is not None and self.reranker is not None
        t0 = time.perf_counter()
        candidates = self.engine.similar_to(movie_id, top_n=max(50, top_n * 5))
        if not candidates:
            return None
        candidates = self.reranker.rerank(candidates)[:top_n]
        movies = self.dataset.movies.set_index("movie_id")
        seed_row = movies.loc[movie_id]
        enriched = []
        for c in candidates:
            mrow = movies.loc[c.movie_id]
            ex = explain(
                seed_id=movie_id, candidate=c,
                content_model=self.engine.content,
                title_lookup=self._title_lookup,
            )
            enriched.append({
                "movie_id": c.movie_id,
                "title": str(mrow["title"]),
                "year": (int(mrow["year"]) if not _is_na(mrow["year"]) else None),
                "score": float(c.score),
                "reason": ex.reason,
                "signals": ex.signals,
            })
        return RecommendationResult(
            seed_id=movie_id,
            seed_title=str(seed_row["title"]),
            seed_genres=str(seed_row["genres"]),
            seed_year=(int(seed_row["year"]) if not _is_na(seed_row["year"]) else None),
            recommendations=enriched,
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )

    def recommend_for_user(self, user_id: int, top_n: int = 10, strategy: str = "content") -> dict | None:
        print(f"[recommend_for_user] called for user {user_id}, strategy={strategy}, personal_ready={self.personal_ready}")
        if not self.personal_ready:
            return None
        assert self.personal_content is not None and self.personal_collab is not None
        t0 = time.perf_counter()

        if strategy == "content":
            recs = self.personal_content.recommend_for_user(user_id, top_n=top_n)
            items = [{"movie_id": r.movie_id, "title": r.title, "score": r.score, "source": "content"} for r in recs]
        elif strategy == "collab":
            recs = self.personal_collab.recommend_for_user(user_id, top_n=top_n)
            items = [{"movie_id": r.movie_id, "title": r.title, "score": r.pred_rating / 5.0,
                      "pred_rating": r.pred_rating, "avg_rating": r.avg_rating,
                      "rating_count": r.rating_count, "source": "collab"} for r in recs]
        elif strategy == "hybrid":
            content_recs = self.personal_content.recommend_for_user(user_id, top_n=top_n * 2)
            collab_recs = self.personal_collab.recommend_for_user(user_id, top_n=top_n * 2)
            blended: dict[int, dict] = {}
            for r in content_recs:
                blended[r.movie_id] = {"movie_id": r.movie_id, "title": r.title,
                                       "content_score": r.score, "collab_score": 0.0, "source": "hybrid"}
            for r in collab_recs:
                entry = blended.setdefault(r.movie_id, {"movie_id": r.movie_id, "title": r.title,
                                                        "content_score": 0.0, "source": "hybrid"})
                entry["collab_score"] = r.pred_rating / 5.0
                entry["pred_rating"] = r.pred_rating
            for v in blended.values():
                v["score"] = 0.5 * v["content_score"] + 0.5 * v["collab_score"]
            items = sorted(blended.values(), key=lambda x: -x["score"])[:top_n]
        else:
            return None

        return {"user_id": user_id, "strategy": strategy, "results": items,
                "latency_ms": int((time.perf_counter() - t0) * 1000)}

    def taste_profile_for(self, user_id: int) -> dict | None:
        if not self.personal_ready:
            return None
        assert self.taste_profiler is not None and self.dataset is not None
        prof = self.taste_profiler.profile(user_id, self.dataset.ratings)
        if not prof.top_genres and not prof.top_cast:
            return None
        return {"user_id": user_id, "top_genres": prof.top_genres, "top_keywords": prof.top_keywords,
                "top_cast": prof.top_cast, "top_directors": prof.top_directors, "top_production": prof.top_production}


def _is_na(v) -> bool:
    try:
        import pandas as pd
        return bool(pd.isna(v))
    except Exception:
        return v is None


print("[service module] creating module-level singleton")
service = RecommendationService()
print(f"[service module] singleton created with id={id(service)}")