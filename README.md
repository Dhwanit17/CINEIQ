<div align="center">

# 🎬 CINE-IQ

**Open, Explainable Movie Recommendation Engine**

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115.4-teal) ![React](https://img.shields.io/badge/React-18.3.1-61DAFB) ![scikit--learn](https://img.shields.io/badge/scikit--learn-Deployed-orange) ![Status](https://img.shields.io/badge/Status-Active-brightgreen)

</div>

---

## Overview

**CINE-IQ** is a transparent, production-ready movie recommendation system designed to answer the question every streaming user asks: *"Why was this recommended to me?"* It combines three classical ML techniques — TF-IDF content similarity, NMF collaborative filtering, and SVD matrix factorization — into a weighted hybrid ensemble, then applies a VADER-powered sentiment re-ranker to surface recommendations people actually enjoy. Every result ships with a human-readable explanation and a per-algorithm signal breakdown, replacing the "black box" with a glass box.

Built by **Krish Patel**.

## Key Features

- **Hybrid Ensemble Engine:** Weighted fusion of three complementary models (Content 40%, Collaborative 40%, Matrix 20%), configurable in a single `config.py` without touching model code.
- **Sentiment Re-Ranking:** VADER lexicon scorer adjusts recommendation scores by ±15% based on user review sentiment — sub-millisecond latency with no training required.
- **Explainability Layer:** Rule-based prose templates produce natural-language reasons ("Shares themes of sci-fi dystopia with…") alongside optional LIME feature attributions for deep-dive analysis.
- **Personal Recommendations:** Per-user strategy (content, collaborative, or hybrid) powered by NMF user factors and TMDB-enriched metadata.
- **Taste Profiler:** Derives a user's top genres, cast, directors, keywords, and production companies from their rating history via the `/explore/user/{id}` endpoint.
- **Live SOC-Style Dashboard:** Streamlit analytics interface with Plotly charts for model performance, dataset statistics, and user taste visualization.

## System Architecture

CINE-IQ operates on a decoupled microservices architecture to keep per-request latency under 100ms after warm-up:

1. **Client Interface (React Frontend):** Terminal-style UI intercepts the movie query and acts as the initial request trigger.
2. **The Orchestrator (FastAPI Backend):** Manages concurrent model inference, TMDB metadata joins, and VADER scoring on a single async request.
3. **Decision Engine:**
   - Layer 1: **Content Model** — TF-IDF genre/tag vectors + cosine similarity (item-item).
   - Layer 2: **Collaborative Model** — sklearn NMF item factor dot product.
   - Layer 3: **Matrix Model** — TruncatedSVD on the full user-item ratings matrix.
   - Layer 4: **Sentiment Re-Ranker** — VADER score adjustment as a post-processing pass.
4. **Explainability Pipeline:** Template-based prose generation with optional LIME attribution per recommendation pair.
5. **Analyst Dashboard (Streamlit):** Real-time model stats, score distribution charts, and user taste profiling.

## Project Structure

```
CINE-IQ/
├── backend/
│   ├── src/cineiq/
│   │   ├── api/
│   │   │   ├── main.py              # FastAPI app, CORS, lifespan handler
│   │   │   ├── routes.py            # /health, /search, /recommend, /similar, /user/*
│   │   │   ├── service.py           # RecommendationService (fits models on startup)
│   │   │   └── schemas.py           # Pydantic request/response models
│   │   ├── models/
│   │   │   ├── content.py           # TF-IDF + cosine similarity
│   │   │   ├── collaborative.py     # sklearn NMF item factors
│   │   │   ├── matrix.py            # TruncatedSVD on user-item matrix
│   │   │   └── hybrid.py            # Weighted ensemble fusion
│   │   ├── sentiment/
│   │   │   ├── vader.py             # VADER lexicon scorer
│   │   │   ├── distilbert.py        # Stub for transformer-based scoring
│   │   │   └── reranker.py          # SentimentReRanker post-processor
│   │   ├── explain/
│   │   │   ├── templates.py         # Rule-based explanation prose
│   │   │   ├── lime_explainer.py    # LIME feature attribution
│   │   │   └── taste_profile.py     # User taste profiler
│   │   ├── data/
│   │   │   ├── loader.py            # MovieLens 100K/25M dataset loader
│   │   │   └── download_tmdb.py     # Optional TMDB metadata fetcher
│   │   ├── tracking/
│   │   │   └── mlflow.py            # MLflow experiment logging
│   │   └── config.py                # Central config (weights, paths, toggles)
│   ├── scripts/
│   │   ├── train.py                 # Offline fit + MLflow logging
│   │   ├── evaluate.py              # Hit-rate@K validation
│   │   └── smoke_test.py            # Quick sanity check
│   ├── streamlit_app/
│   │   └── dashboard.py             # Streamlit analytics dashboard
│   ├── tests/                       # pytest suite (synthetic 30-movie fixture)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx                  # Top-level component composition
│       ├── components/
│       │   ├── Hero.jsx             # Landing hero with glitch animation
│       │   ├── Demo.jsx             # Interactive terminal demo
│       │   ├── Features.jsx         # Feature cards
│       │   ├── Architecture.jsx     # ML pipeline diagram
│       │   └── Stack.jsx            # Technology showcase
│       ├── hooks/
│       │   ├── useScrollReveal.js   # IntersectionObserver fade-in
│       │   └── useScrollNav.js      # Scroll-tracking nav state
│       └── data/                    # Hardcoded demo & ticker content
├── artifacts/                       # Model checkpoints (gitignored)
└── data/                            # MovieLens dataset (gitignored)
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service status, model readiness, dataset stats |
| `GET` | `/search?q={query}` | Fuzzy movie title search |
| `GET` | `/recommend?title={title}&top_n=10` | Hybrid recommendations by title |
| `GET` | `/recommend?movie_id={id}&top_n=10` | Hybrid recommendations by ID |
| `GET` | `/similar?movie_id={id}` | Item-item similarity lookup |
| `GET` | `/recommend/user/{user_id}?strategy=hybrid` | Personalized user recommendations |
| `GET` | `/explore/user/{user_id}` | User taste profile (genres, cast, directors) |

Each recommendation response includes `score`, `score_pct`, a natural-language `reason`, and a `signals` breakdown (content, collaborative, matrix, sentiment).

## Getting Started

### Backend

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m cineiq.data.download          # Download MovieLens 100K (~5s)
python -m cineiq.data.download_tmdb     # Optional: TMDB metadata

uvicorn cineiq.api.main:app --reload    # API → http://localhost:8000/docs
streamlit run streamlit_app/dashboard.py # Dashboard → http://localhost:8501
```

### Frontend

```bash
cd frontend
npm install
npm run dev                             # UI → http://localhost:5173
```

### Training & Evaluation

```bash
python scripts/train.py                 # Fit models + log to MLflow
python scripts/evaluate.py             # Hit-rate@K validation
mlflow ui                              # Experiment tracker → http://localhost:5000
pytest                                 # Full test suite
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.115.4, Uvicorn, Pydantic |
| ML Core | scikit-learn (NMF, TruncatedSVD, TF-IDF), NumPy, pandas |
| Sentiment | vaderSentiment 3.3.2, LIME 0.2.0.1 |
| Tracking | MLflow 2.17.2 |
| Dashboard | Streamlit 1.39.0, Plotly 5.24.1 |
| Frontend | React 18.3.1, Vite 5.4.0 |
| Data | MovieLens 100K / 25M, TMDB API (optional) |
| Testing | pytest 8.3.3, httpx 0.27.2 |
