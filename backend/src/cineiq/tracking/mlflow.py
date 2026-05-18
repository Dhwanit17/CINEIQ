"""
Minimal MLflow integration.

We log training runs (dataset variant, weights, sub-model params,
fit time) so experiments are reproducible. If `CINEIQ_MLFLOW=0`
the helpers degrade to no-ops, which keeps tests fast and avoids
writing to disk on every import.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from cineiq.config import settings


@contextmanager
def run(run_name: str, params: dict[str, Any] | None = None) -> Iterator[Any]:
    """Context manager that opens an MLflow run, or a no-op if disabled."""
    cfg = settings.tracking
    if not cfg.enabled:
        yield None
        return

    # Lazy import — mlflow pulls in a lot.
    import mlflow

    mlflow.set_tracking_uri(cfg.tracking_uri)
    mlflow.set_experiment(cfg.experiment_name)
    with mlflow.start_run(run_name=run_name) as r:
        if params:
            mlflow.log_params(params)
        yield r


def log_metric(name: str, value: float) -> None:
    if not settings.tracking.enabled:
        return
    import mlflow
    mlflow.log_metric(name, value)


def log_artifact(path: str) -> None:
    if not settings.tracking.enabled:
        return
    import mlflow
    mlflow.log_artifact(path)
