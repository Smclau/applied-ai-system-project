"""Edge case tests for the recommender and evaluator."""

import pytest
from src.recommender import recommend_songs, load_songs
from src.evaluator import check_strategy_agreement, check_score_spread

_PROFILE = {
    "favorite_genre":      "lofi",
    "favorite_mood":       "chill",
    "target_energy":       0.40,
    "target_acousticness": 0.70,
}


@pytest.fixture
def songs():
    return load_songs("data/songs.csv")


# --- recommend_songs ---

def test_k_larger_than_catalog_returns_all(songs):
    results = recommend_songs(_PROFILE, songs, k=9999)
    assert len(results) == len(songs)


def test_empty_catalog_returns_empty():
    results = recommend_songs(_PROFILE, [], k=5)
    assert results == []


def test_k_zero_returns_empty(songs):
    results = recommend_songs(_PROFILE, songs, k=0)
    assert results == []


def test_unknown_strategy_falls_back(songs):
    # Should not raise — silently uses energy-first
    results = recommend_songs(_PROFILE, songs, k=5, strategy="nonexistent")
    assert len(results) == 5


def test_results_are_sorted_descending(songs):
    results = recommend_songs(_PROFILE, songs, k=5)
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)


# --- evaluator ---

def test_strategy_agreement_k_zero_no_crash(songs):
    result = check_strategy_agreement(_PROFILE, songs, k=0)
    assert result == 0.0


def test_strategy_agreement_empty_catalog():
    result = check_strategy_agreement(_PROFILE, [], k=5)
    assert result == 0.0


def test_score_spread_empty_catalog():
    result = check_score_spread(_PROFILE, [])
    assert result == 0.0


def test_score_spread_single_song(songs):
    result = check_score_spread(_PROFILE, [songs[0]])
    assert result == 0.0
