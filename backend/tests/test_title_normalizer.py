"""Unit tests for the title normalizer that powers the MovieLens<->TMDB join."""
from __future__ import annotations

from cineiq.data.enriched import _normalize_title


def test_strip_year():
    assert _normalize_title("Toy Story (1995)") == "toy story"
    assert _normalize_title("Star Wars (1977)") == "star wars"


def test_trailing_article_the():
    # MovieLens style: "Empire Strikes Back, The (1980)"
    # TMDB style:      "The Empire Strikes Back"
    assert _normalize_title("Empire Strikes Back, The (1980)") == "the empire strikes back"


def test_trailing_article_il():
    # The notorious "Postino, Il" pattern
    assert _normalize_title("Postino, Il (1994)") == "il postino"


def test_trailing_article_la_le():
    assert _normalize_title("Haine, La (1995)") == "la haine"
    assert _normalize_title("Samourai, Le (1967)") == "le samourai"


def test_punctuation_stripped():
    # Apostrophes and colons vary between sources
    assert _normalize_title("Schindler's List (1993)") == "schindlers list"
    assert _normalize_title("Mr. Smith Goes to Washington") == "mr smith goes to washington"


def test_idempotent_on_clean_titles():
    # TMDB titles are already clean — shouldn't break them
    assert _normalize_title("The Godfather") == "the godfather"
    assert _normalize_title("Pulp Fiction") == "pulp fiction"


def test_empty_and_none():
    assert _normalize_title("") == ""
    assert _normalize_title(None) == ""  # type: ignore[arg-type]


def test_normalizer_matches_on_problem_titles():
    """The actual point of the normalizer: ML and TMDB versions should match."""
    pairs = [
        ("Empire Strikes Back, The (1980)", "The Empire Strikes Back"),
        ("Postino, Il (1994)", "Il Postino"),
        ("Princess Bride, The (1987)", "The Princess Bride"),
        ("Usual Suspects, The (1995)", "The Usual Suspects"),
        ("Lord of the Rings, The (1978)", "The Lord of the Rings"),
    ]
    for ml_title, tmdb_title in pairs:
        assert _normalize_title(ml_title) == _normalize_title(tmdb_title), \
            f"Failed to match: {ml_title!r} vs {tmdb_title!r}"
