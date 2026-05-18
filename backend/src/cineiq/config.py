"""
Central config for CINEIQ.

Everything that might change between environments (paths, ensemble weights,
model toggles) lives here. Importable from any module.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ----- Paths -----
ROOT = Path(__file__).resolve().parents[2].parent  # cineiq-backend/
DATA_DIR = ROOT / "data"
ARTIFACTS_DIR = ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class DatasetConfig:
    """MovieLens dataset to load.

    Switching scale = changing the `variant` only. Everything downstream
    reads paths from the loader, not from hardcoded filenames.
    """

    variant: str = "ml-100k"   # ← change to "ml-25m" when ready
    movies_file: str = "u.item"
    ratings_file: str = "u.data"
    sep: str = "|"             # ml-100k uses | for movies, \t for ratings
    encoding: str = "latin-1"  # ml-100k is latin-1, not utf-8

    @property
    def root(self) -> Path:
        return DATA_DIR / self.variant


@dataclass(frozen=True)
class HybridWeights:
    """Weights for the ensemble. Must sum to ~1.0 (we normalize anyway)."""

    collaborative: float = 0.4   # Surprise SVD on user-item ratings
    content: float = 0.4         # TF-IDF + cosine on movie text
    matrix: float = 0.2          # scikit-learn TruncatedSVD on user-item


@dataclass(frozen=True)
class SentimentConfig:
    """Sentiment re-ranking knobs."""

    enabled: bool = True
    backend: str = "vader"       # "vader" | "distilbert" (stub)
    # How much sentiment is allowed to shift a recommendation's score
    influence: float = 0.15


@dataclass(frozen=True)
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    # CORS — the React dev server runs on 5173 by default
    allowed_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    )


@dataclass(frozen=True)
class TrackingConfig:
    enabled: bool = bool(int(os.getenv("CINEIQ_MLFLOW", "1")))
    experiment_name: str = "cineiq"
    tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", str(ROOT / "mlruns"))


@dataclass(frozen=True)
class Config:
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    weights: HybridWeights = field(default_factory=HybridWeights)
    sentiment: SentimentConfig = field(default_factory=SentimentConfig)
    api: APIConfig = field(default_factory=APIConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)

    # How many candidates each sub-model contributes before fusion
    candidate_pool_size: int = 200
    # Default top-N returned to the user
    default_top_n: int = 10


# Single shared instance. Override in tests by constructing your own Config().
settings = Config()
