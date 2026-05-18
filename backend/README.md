# CINEIQ — Backend

The open, explainable movie recommendation engine described in the
project spec: hybrid CF + content + matrix-SVD, sentiment re-ranker,
LIME explanations, MLflow tracking, FastAPI serving, Streamlit dashboard.

This is the **scaffold** — every module is real and tested, but it's
sized for fast iteration on MovieLens 100K. Swap config knobs to scale
up to 25M, add DistilBERT for sentiment, plug in TMDB metadata, etc.

## Quick start

```bash
# 1. Install
python -m venv .venv && source .venv/bin/activate
pip install -e .                  # uses pyproject.toml
pip install -r requirements.txt

# 2. Get MovieLens data (5 MB, ~5 seconds) — required
python -m cineiq.data.download

# 3. Get TMDB data (~10 MB) — optional, enables personal models
python -m cineiq.data.download_tmdb

# 4. Run the API
uvicorn cineiq.api.main:app --reload
# → http://localhost:8000/docs

# 5. (Optional) Run the Streamlit dashboard
streamlit run streamlit_app/dashboard.py
# → http://localhost:8501

# 6. (Optional) Train offline + log to MLflow
python scripts/train.py
mlflow ui                          # → http://localhost:5000
```

The API warms up the models on startup. On 100K that takes ~10 seconds
(item-item) plus another ~20 seconds (personal models, if TMDB is present).
Once warm, every request is sub-100ms.

If TMDB data isn't downloaded, the personal endpoints return 503 with a
helpful error message; the item-item endpoints work as normal.

## API endpoints

**Item-item (no TMDB required):**

- `GET /health` — readiness + dataset stats
- `GET /search?q=blade` — substring movie search
- `GET /recommend?title=Star+Wars+(1977)&top_n=10` — similar movies, by title
- `GET /recommend?movie_id=50&top_n=10` — same, by id
- `GET /similar?movie_id=50&top_n=10` — alias kept distinct because spec names both

**Personal / user-level (TMDB required):**

- `GET /recommend/user/{user_id}?strategy=hybrid` — personalized recommendations
   - `strategy` is one of `content`, `collab`, `hybrid`
- `GET /explore/user/{user_id}` — top genres, cast, directors, keywords for that user

Swagger docs at `/docs`.

All recommendations come with:
- `score` (0-1) and `score_pct` (0-100)
- `reason` — human-readable string with `<span class="hl">…</span>` highlights
- `signals` — per-model contributions (content, collaborative, matrix, sentiment)

## Architecture

```
                ┌────────────┐
                │ MovieLens  │  (downloaded into data/)
                │ 100K / 25M │
                └─────┬──────┘
                      │
                      ▼
          ┌───────────────────────┐
          │  cineiq.data.loader   │  ← single contract: Dataset(ratings, movies)
          └───────────┬───────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   ContentModel  CollaborativeModel  MatrixModel
   (TF-IDF +    (sklearn NMF →      (sklearn SVD on
    cosine)      item factors)       user-item matrix)
        │             │             │
        └─────────────┼─────────────┘
                      ▼
              HybridEngine            ← weighted fusion → ScoreMap
                      │
                      ▼
            SentimentReRanker         ← VADER over reviews (cache)
                      │
                      ▼
             explain.templates        ← human reason + signals dict
                      │
                      ▼
                FastAPI /recommend    ← Pydantic-validated response
```

The Streamlit dashboard imports the same modules — it's a second front
end, not a parallel implementation.

## Project layout

```
cineiq-backend/
├── README.md
├── pyproject.toml                # editable install via `pip install -e .`
├── requirements.txt
├── data/                         # gitignored, downloaded by data.download
├── artifacts/                    # gitignored, output of scripts/train.py
├── scripts/
│   ├── train.py                  # fit + persist + MLflow run
│   └── evaluate.py               # hit-rate@K sanity check
├── streamlit_app/
│   └── dashboard.py
├── src/cineiq/
│   ├── config.py                 # ALL paths, weights, toggles
│   ├── data/
│   │   ├── download.py
│   │   └── loader.py
│   ├── models/
│   │   ├── base.py               # SimilarityModel Protocol
│   │   ├── content.py            # TF-IDF + cosine
│   │   ├── collaborative.py      # sklearn NMF item factors
│   │   ├── matrix.py             # sklearn TruncatedSVD
│   │   └── hybrid.py             # weighted ensemble
│   ├── sentiment/
│   │   ├── base.py
│   │   ├── vader.py
│   │   ├── distilbert.py         # STUB; 5-line activation recipe inside
│   │   └── reranker.py
│   ├── explain/
│   │   ├── templates.py          # rule-based reasons (cheap)
│   │   └── lime_explainer.py     # LIME-based attribution (per-pair)
│   ├── tracking/
│   │   └── mlflow.py
│   └── api/
│       ├── main.py               # FastAPI app + lifespan
│       ├── routes.py
│       ├── service.py            # singleton holding fitted models
│       └── schemas.py            # Pydantic
└── tests/
    ├── conftest.py               # tiny synthetic dataset fixture
    ├── test_models.py
    ├── test_sentiment_and_explain.py
    └── test_api.py
```

## Configuration

All knobs live in `src/cineiq/config.py`:

| Field                              | Default       | What it does                          |
|------------------------------------|---------------|---------------------------------------|
| `dataset.variant`                  | `"ml-100k"`   | `"ml-25m"` for full scale             |
| `weights.collaborative`            | `0.4`         | NMF weight in ensemble                |
| `weights.content`                  | `0.4`         | TF-IDF weight                         |
| `weights.matrix`                   | `0.2`         | sklearn SVD weight                    |
| `sentiment.backend`                | `"vader"`     | `"distilbert"` once you wire it       |
| `sentiment.influence`              | `0.15`        | Max ± shift sentiment can apply       |
| `candidate_pool_size`              | `200`         | Per-model candidates before fusion    |

Environment variables:
- `CINEIQ_MLFLOW=0` — disable MLflow logging
- `MLFLOW_TRACKING_URI` — point MLflow at a remote tracking server
- `VITE_CINEIQ_API_URL` — (frontend) override the API host

## Wiring the React frontend

The Demo component in `cineiq-react/` will call `http://localhost:8000/recommend`
automatically. When the API is unreachable it falls back to the hardcoded
`demoData` dictionary and shows `SOURCE = LOCAL_CACHE` in the result banner.

To point the built frontend at a deployed API:

```bash
VITE_CINEIQ_API_URL=https://api.cineiq.example.com npm run build
```

## Scaling up

- **MovieLens 25M**: `python -m cineiq.data.download --variant ml-25m` then set
  `dataset.variant = "ml-25m"` in `config.py`. The loader handles both formats.
- **DistilBERT sentiment**: see the 5-line recipe at the top of
  `cineiq/sentiment/distilbert.py`. Needs `torch` + `transformers`.
- **TMDB metadata**: write a `data/tmdb.py` loader that returns
  `(movie_id, cast, crew, keywords, plot)`; append the plot/keywords to the
  movies' `content_text` before passing to the loader. ContentModel will
  pick up the richer vocabulary automatically.
- **IMDB 50K reviews → sentiment cache**: pass `reviews_by_movie` into
  `SentimentReRanker.warm_cache()` once at startup (currently done in
  `service.warm_up()` — extend it to load and cache).

## Tests

```bash
pytest                             # all
pytest tests/test_models.py -v     # model-only
pytest -k "not api"                # skip the full FastAPI integration tests
```

Model tests run on a 30-movie synthetic dataset, so they're fast and
don't need MovieLens downloaded.
