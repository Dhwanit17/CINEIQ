"""
LIME-based feature attribution.

LIME is most useful when the content model is doing the heavy lifting.
We perturb the seed movie's content_text and watch how the cosine
similarity to a target candidate moves — the terms with the highest
positive attribution are the ones "explaining" the match.

This is more expensive than the rule-based templates (LIME runs ~5000
perturbations by default) so we expose it behind an explicit endpoint
rather than running it for every recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from lime.lime_text import LimeTextExplainer
from sklearn.metrics.pairwise import linear_kernel

from cineiq.data.loader import Dataset
from cineiq.models.content import ContentModel


@dataclass
class LimeAttribution:
    seed_id: int
    candidate_id: int
    terms: list[tuple[str, float]]


def lime_explain_content(
    seed_id: int,
    candidate_id: int,
    content: ContentModel,
    dataset: Dataset,
    num_features: int = 8,
    num_samples: int = 1000,
) -> LimeAttribution:
    """Run LIME on the content model for one (seed -> candidate) pair."""
    if content.matrix is None:
        raise RuntimeError("ContentModel must be fitted before calling lime_explain_content")

    movies = dataset.movies.set_index("movie_id")
    seed_text = str(movies.loc[seed_id, "content_text"])
    cand_row = content._id_to_row[candidate_id]
    cand_vec = content.matrix[cand_row]

    def predict_proba(texts: list[str]) -> np.ndarray:
        # LIME wants class probabilities. We use cosine to the candidate
        # as a single "score", then turn it into a fake 2-class problem.
        vecs = content.vectorizer.transform(texts)
        sims = linear_kernel(vecs, cand_vec).ravel()
        # Clip and present as [P(not_match), P(match)]
        sims = np.clip(sims, 0.0, 1.0)
        return np.column_stack([1 - sims, sims])

    explainer = LimeTextExplainer(class_names=["not_match", "match"])
    exp = explainer.explain_instance(
        seed_text,
        predict_proba,
        num_features=num_features,
        num_samples=num_samples,
        labels=[1],
    )
    return LimeAttribution(
        seed_id=seed_id,
        candidate_id=candidate_id,
        terms=[(str(term), float(weight)) for term, weight in exp.as_list(label=1)],
    )
