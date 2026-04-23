"""
Reliability evaluator for the music recommender.

Three checks per profile:
  1. Determinism  — identical input always produces identical ranked output.
  2. Score spread — gap between the #1 and #5 scores (narrow = low confidence).
  3. Strategy agreement — % of songs shared across all three scoring strategies.

Run via:  python3 -m src.main --evaluate
"""

import logging
from typing import Dict, List

from tabulate import tabulate

from .recommender import recommend_songs, STRATEGIES

logger = logging.getLogger(__name__)

_N_DETERMINISM_RUNS = 10
_SPREAD_HIGH = 0.10   # score gap threshold for High confidence
_SPREAD_LOW  = 0.03   # score gap threshold for Low confidence
_AGREE_HIGH  = 0.80   # strategy overlap threshold for High confidence
_AGREE_LOW   = 0.40   # strategy overlap threshold for Low confidence


def check_determinism(profile: Dict, songs: List[Dict], n_runs: int = _N_DETERMINISM_RUNS) -> bool:
    """Return True if n_runs identical calls all produce the same ranking."""
    baseline = [s["id"] for s, _, _ in recommend_songs(profile, songs)]
    for _ in range(n_runs - 1):
        result = [s["id"] for s, _, _ in recommend_songs(profile, songs)]
        if result != baseline:
            logger.warning("Non-deterministic result detected for profile %s", profile)
            return False
    return True


def check_score_spread(profile: Dict, songs: List[Dict]) -> float:
    """Return the score gap between the #1 and #5 recommendations (energy-first)."""
    results = recommend_songs(profile, songs, k=5)
    if len(results) < 2:
        return 0.0
    return round(results[0][1] - results[-1][1], 4)


def check_strategy_agreement(profile: Dict, songs: List[Dict], k: int = 5) -> float:
    """Return fraction of top-k songs that appear in ALL three strategy results."""
    sets = []
    for strategy in STRATEGIES:
        ids = {s["id"] for s, _, _ in recommend_songs(profile, songs, k=k, strategy=strategy)}
        sets.append(ids)
    intersection = sets[0] & sets[1] & sets[2]
    return round(len(intersection) / k, 2)


def _confidence(spread: float, agreement: float) -> str:
    if spread >= _SPREAD_HIGH and agreement >= _AGREE_HIGH:
        return "High"
    if spread <= _SPREAD_LOW or agreement <= _AGREE_LOW:
        return "Low"
    return "Medium"


def run_full_evaluation(profiles: Dict[str, Dict], songs: List[Dict]) -> None:
    """Run all reliability checks across all profiles and print a summary table."""
    logger.info("Starting reliability evaluation across %d profiles", len(profiles))

    rows = []
    for name, profile in profiles.items():
        deterministic = check_determinism(profile, songs)
        spread        = check_score_spread(profile, songs)
        agreement     = check_strategy_agreement(profile, songs)
        confidence    = _confidence(spread, agreement)

        logger.info(
            "Profile=%r deterministic=%s spread=%.4f agreement=%.2f confidence=%s",
            name, deterministic, spread, agreement, confidence,
        )

        rows.append([
            name,
            "✓" if deterministic else "✗",
            f"{spread:.3f}",
            f"{agreement * 100:.0f}%",
            confidence,
        ])

    print(f"\n{'='*65}")
    print("  Reliability Evaluation Report")
    print(f"{'='*65}")
    print(tabulate(
        rows,
        headers=["Profile", "Deterministic", "Score Spread", "Strategy Agree", "Confidence"],
        tablefmt="rounded_outline",
    ))
    print()

    n_high   = sum(1 for r in rows if r[4] == "High")
    n_low    = sum(1 for r in rows if r[4] == "Low")
    n_nondet = sum(1 for r in rows if r[1] == "✗")

    print(f"  Summary: {n_high}/{len(rows)} High confidence  |  "
          f"{n_low}/{len(rows)} Low confidence  |  "
          f"{n_nondet} non-deterministic")
    print()

    if n_nondet:
        print("  WARNING: non-deterministic results detected — scoring logic may have hidden randomness.")
    if n_low:
        print("  NOTE: Low-confidence profiles have a narrow score spread or low strategy agreement.")
        print("        Consider expanding the song catalog for those genres/moods.")
    print()

    logger.info(
        "Evaluation complete | high=%d low=%d non_det=%d",
        n_high, n_low, n_nondet,
    )
