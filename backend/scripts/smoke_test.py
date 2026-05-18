"""
Smoke test: boot the FastAPI app in-process with a synthetic dataset and
exercise every endpoint. This verifies the full stack (routes →
service → hybrid engine → reranker → templates → pydantic) end to end
without needing MovieLens downloaded.
"""
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

from cineiq.data.loader import Dataset
from cineiq.api.main import app
from cineiq.api import service as service_mod
from cineiq.models.hybrid import HybridEngine
from cineiq.sentiment.reranker import SentimentReRanker


def build_dataset() -> Dataset:
    rng = np.random.default_rng(0)
    sci_fi = [(i, f"SciFi Title {i}", 2000 + i % 20, "Sci-Fi Action")
              for i in range(1, 16)]
    comedy = [(i + 100, f"Comedy Title {i}", 1990 + i % 25, "Comedy Romance")
              for i in range(1, 16)]
    rows = sci_fi + comedy
    movies = pd.DataFrame(rows, columns=["movie_id", "title", "year", "genres"])
    movies["content_text"] = (
        movies["title"] + " " + movies["year"].astype(str) + " " + movies["genres"]
    )
    records = []
    for u in range(1, 41):
        loves_scifi = u <= 25
        for mid in movies["movie_id"]:
            if rng.random() > 0.4:
                continue
            is_scifi = mid < 100
            if loves_scifi:
                r = rng.integers(4, 6) if is_scifi else rng.integers(1, 4)
            else:
                r = rng.integers(4, 6) if not is_scifi else rng.integers(1, 4)
            records.append((u, int(mid), int(r), 0))
    ratings = pd.DataFrame(records, columns=["user_id", "movie_id", "rating", "timestamp"])
    return Dataset(ratings=ratings, movies=movies)


def main() -> None:
    print("=" * 60)
    print("CINEIQ END-TO-END SMOKE TEST")
    print("=" * 60)

    # Pre-fit the service against synthetic data, bypassing the lifespan
    ds = build_dataset()
    svc = service_mod.service
    svc.dataset = ds
    svc.engine = HybridEngine().fit(ds)
    svc.reranker = SentimentReRanker()
    svc._title_lookup = dict(
        zip(ds.movies["movie_id"].astype(int), ds.movies["title"].astype(str))
    )

    # Disable the lifespan so we don't try to download MovieLens
    app.router.lifespan_context = None

    client = TestClient(app)

    print("\n--- GET /health ---")
    r = client.get("/health")
    print(f"status={r.status_code}")
    print(r.json())

    print("\n--- GET /search?q=SciFi&limit=3 ---")
    r = client.get("/search", params={"q": "SciFi", "limit": 3})
    print(f"status={r.status_code}")
    for m in r.json()["results"]:
        print(f"  {m}")

    print("\n--- GET /recommend?title=SciFi Title 1&top_n=5 ---")
    r = client.get("/recommend", params={"title": "SciFi Title 1", "top_n": 5})
    print(f"status={r.status_code}")
    body = r.json()
    print(f"meta: {body['meta']}")
    print(f"results ({len(body['results'])}):")
    for rec in body["results"]:
        print(f"  [{rec['score_pct']}%] {rec['title']} ({rec['year']})")
        print(f"        reason: {rec['reason']}")
        print(f"        signals: {rec['signals']}")

    print("\n--- GET /similar?movie_id=101&top_n=3 ---")
    r = client.get("/similar", params={"movie_id": 101, "top_n": 3})
    print(f"status={r.status_code}")
    for rec in r.json()["results"]:
        print(f"  [{rec['score_pct']}%] {rec['title']}")

    print("\n--- GET /recommend?title=Nonexistent ---")
    r = client.get("/recommend", params={"title": "Nonexistent"})
    print(f"status={r.status_code} (expecting 404)")
    print(f"body={r.json()}")

    print("\n--- GET /recommend (missing params) ---")
    r = client.get("/recommend")
    print(f"status={r.status_code} (expecting 422)")

    print("\n--- GET /recommend/user/1 (no TMDB - should 503) ---")
    r = client.get("/recommend/user/1")
    print(f"status={r.status_code} (expecting 503 since TMDB isn't loaded)")
    print(f"body={r.json()}")

    print("\n--- GET /explore/user/1 (no TMDB - should 503) ---")
    r = client.get("/explore/user/1")
    print(f"status={r.status_code} (expecting 503 since TMDB isn't loaded)")

    print("\n" + "=" * 60)
    print("ALL ENDPOINTS RESPONDED")
    print("=" * 60)


if __name__ == "__main__":
    main()
