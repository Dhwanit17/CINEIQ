"""
Rule-based explanation templates.

LIME is great for ML-side feature attribution, but users don't want to
read coefficients. So we wrap the model signals in templated prose,
plus a structured `signals` dict so the frontend can render bars.

Hierarchy of explanation strength:
  1. If content was the dominant signal AND we have shared TF-IDF terms,
     name the terms ("shared themes of <terms>").
  2. If collaborative dominated, frame as audience overlap.
  3. If matrix dominated, frame as latent taste.
  4. Sentiment can be appended as a modifier.
"""
from __future__ import annotations

from dataclasses import dataclass

from cineiq.models.content import ContentModel
from cineiq.models.hybrid import Candidate


@dataclass
class Explanation:
    reason: str
    signals: dict[str, float]


def _dominant(components: dict[str, float]) -> tuple[str, float]:
    if not components:
        return ("unknown", 0.0)
    return max(components.items(), key=lambda kv: kv[1])


def explain(
    seed_id: int,
    candidate: Candidate,
    content_model: ContentModel,
    title_lookup: dict[int, str],
) -> Explanation:
    """Build a human-readable reason for why `candidate` was recommended."""
    seed_title = title_lookup.get(seed_id, "this film")
    cand_title = title_lookup.get(candidate.movie_id, "this recommendation")
    dominant_name, dominant_score = _dominant(
        {k: v for k, v in candidate.components.items() if k != "sentiment"}
    )

    sentiment = candidate.components.get("sentiment", 0.0)

    if dominant_name == "content":
        terms = content_model.shared_terms(seed_id, candidate.movie_id, k=4)
        if terms:
            term_str = ", ".join(f"<span class='hl'>{t}</span>" for t in terms)
            reason = f"Shares {term_str} with {seed_title}."
        else:
            reason = f"Similar themes and genre profile to {seed_title}."

    elif dominant_name == "collaborative":
        reason = (
            f"Audiences who rated {seed_title} highly also gravitate to "
            f"<span class='hl'>{cand_title}</span> — collaborative-filtering signal."
        )

    elif dominant_name == "matrix":
        reason = (
            f"Maps to the same <span class='hl'>latent taste region</span> "
            f"as {seed_title} in our SVD factor space."
        )
    else:
        reason = f"Cross-signal match with {seed_title}."

    if sentiment >= 0.4:
        reason += " Reviews skew strongly positive."
    elif sentiment <= -0.3:
        reason += " Note: review sentiment is mixed."

    return Explanation(
        reason=reason,
        signals={**candidate.components},
    )
