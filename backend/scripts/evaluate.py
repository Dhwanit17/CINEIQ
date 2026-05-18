"""
Lightweight offline evaluation.

For each user with >= 10 ratings, hold out 20% of their ratings, train
on the rest, and check how many of the held-out items the hybrid engine
recommends when seeded with one of their highly-rated remaining items.

This is the bare minimum to compare model configs; for proper evaluation
you'd want NDCG, MAP, item coverage, intra-list diversity.

Usage:
    python scripts/evaluate.py
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np
import pandas as pd

from cineiq.data.loader import load_dataset
from cineiq.models.hybrid import HybridEngine
from cineiq.tracking import mlflow as track


def main() -> int:
    dataset = load_dataset()
    ratings = dataset.ratings.copy()

    # Keep users with enough history
    counts = ratings.groupby("user_id").size()
    keep_users = counts[counts >= 10].index
    ratings = ratings[ratings["user_id"].isin(keep_users)]
    print(f"[eval] users with >=10 ratings: {len(keep_users)}")

    rng = np.random.default_rng(42)
    train_rows = []
    test_rows = []
    for uid, group in ratings.groupby("user_id"):
        shuffled = group.sample(frac=1.0, random_state=int(uid) % 2**32)
        n_test = max(1, int(len(shuffled) * 0.2))
        test_rows.append(shuffled.iloc[:n_test])
        train_rows.append(shuffled.iloc[n_test:])

    train_df = pd.concat(train_rows, ignore_index=True)
    test_df = pd.concat(test_rows, ignore_index=True)

    held_out = defaultdict(set)
    for uid, mid in zip(test_df["user_id"], test_df["movie_id"]):
        held_out[int(uid)].add(int(mid))

    # Fit on the train split
    train_dataset = type(dataset)(ratings=train_df, movies=dataset.movies)
    engine = HybridEngine().fit(train_dataset)

    # For each user, pick a high-rated seed from train, see if held-out items appear in top-10
    hits = 0
    total = 0
    K = 10
    sample = rng.choice(list(held_out.keys()), size=min(200, len(held_out)), replace=False)
    for uid in sample:
        user_train = train_df[train_df["user_id"] == uid]
        if user_train.empty:
            continue
        seed_mid = int(user_train.sort_values("rating", ascending=False).iloc[0]["movie_id"])
        recs = engine.similar_to(seed_mid, top_n=K)
        rec_ids = {c.movie_id for c in recs}
        if rec_ids & held_out[uid]:
            hits += 1
        total += 1

    hit_rate = hits / total if total else 0.0
    print(f"[eval] hit-rate@{K} over {total} users: {hit_rate:.3f}")

    with track.run("evaluate_hybrid", params={"K": K, "n_users": total}):
        track.log_metric(f"hit_rate@{K}", hit_rate)

    return 0


if __name__ == "__main__":
    sys.exit(main())
