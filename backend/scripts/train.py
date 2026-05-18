"""
Offline training script.

Fits all models on the configured dataset, persists artifacts under
`artifacts/`, and logs the run to MLflow if enabled.

Usage:
    python scripts/train.py
    python scripts/train.py --variant ml-25m
    CINEIQ_MLFLOW=0 python scripts/train.py   # skip MLflow
"""
from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

from cineiq.config import ARTIFACTS_DIR, settings
from cineiq.data.loader import load_dataset
from cineiq.models.hybrid import HybridEngine
from cineiq.tracking import mlflow as track


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fit CINEIQ hybrid engine")
    parser.add_argument("--variant", default=settings.dataset.variant)
    parser.add_argument("--out", type=Path, default=ARTIFACTS_DIR / "engine.pkl")
    args = parser.parse_args(argv)

    print(f"[load] dataset={args.variant}")
    dataset = load_dataset(args.variant)
    print(f"       n_users={dataset.n_users} n_movies={dataset.n_movies} n_ratings={dataset.n_ratings}")

    params = {
        "dataset": args.variant,
        "weight_content": settings.weights.content,
        "weight_collaborative": settings.weights.collaborative,
        "weight_matrix": settings.weights.matrix,
        "candidate_pool_size": settings.candidate_pool_size,
    }

    with track.run("train_hybrid", params=params):
        t0 = time.perf_counter()
        engine = HybridEngine().fit(dataset)
        fit_seconds = time.perf_counter() - t0
        print(f"[fit ] hybrid engine fitted in {fit_seconds:.2f}s")
        track.log_metric("fit_seconds", fit_seconds)

        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("wb") as f:
            pickle.dump(engine, f)
        print(f"[save] {args.out}")
        track.log_artifact(str(args.out))

    return 0


if __name__ == "__main__":
    sys.exit(main())
