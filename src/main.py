"""
Music Recommender — command-line runner.

Modes:
  default        Run all hardcoded profiles across all scoring strategies (batch output).
  --interactive  Claude-powered agent: describe what you want in plain English.
  --evaluate     Reliability report: determinism, score spread, strategy agreement.

Usage:
  python3 -m src.main                  # batch mode
  python3 -m src.main --interactive    # agent mode (requires ANTHROPIC_API_KEY)
  python3 -m src.main --evaluate       # reliability evaluation
"""

import argparse
import logging
import os
import sys

from tabulate import tabulate

from .recommender import load_songs, recommend_songs


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        handlers=[
            logging.FileHandler("logs/recommender.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _print_recommendations(profile_name: str, strategy: str, recommendations: list) -> None:
    print(f"\n{'='*65}")
    print(f"  {profile_name}  [{strategy}]")
    print(f"{'='*65}")
    rows = [
        [rank, song["title"], song["artist"], f"{score:.2f}", explanation]
        for rank, (song, score, explanation) in enumerate(recommendations, 1)
    ]
    print(tabulate(rows, headers=["#", "Title", "Artist", "Score", "Why"], tablefmt="rounded_outline"))
    print()


_PROFILES = {
    "Chill Lofi Session": {
        "favorite_genre":      "lofi",
        "favorite_mood":       "chill",
        "target_energy":       0.38,
        "target_acousticness": 0.75,
    },
    "Focused Lofi Session": {
        "favorite_genre":      "lofi",
        "favorite_mood":       "focused",
        "target_energy":       0.42,
        "target_acousticness": 0.72,
    },
    "Relaxed Lofi Session": {
        "favorite_genre":      "lofi",
        "favorite_mood":       "relaxed",
        "target_energy":       0.34,
        "target_acousticness": 0.82,
    },
    "Pop Happy Session": {
        "favorite_genre":      "pop",
        "favorite_mood":       "happy",
        "target_energy":       0.80,
        "target_acousticness": 0.20,
    },
    "High-Energy Pop": {
        "favorite_genre":      "pop",
        "favorite_mood":       "energetic",
        "target_energy":       0.90,
        "target_acousticness": 0.08,
    },
    "Deep Intense Rock": {
        "favorite_genre":      "rock",
        "favorite_mood":       "intense",
        "target_energy":       0.92,
        "target_acousticness": 0.10,
    },
    "Sad Acoustic Folk": {
        "favorite_genre":      "folk",
        "favorite_mood":       "sad",
        "target_energy":       0.30,
        "target_acousticness": 0.90,
    },
}


def run_batch(songs: list) -> None:
    profiles = _PROFILES

    for profile_name, user_prefs in profiles.items():
        for strategy in ["energy-first", "genre-first", "mood-first"]:
            recommendations = recommend_songs(user_prefs, songs, k=5, strategy=strategy)
            _print_recommendations(profile_name, strategy, recommendations)


def run_interactive(songs: list) -> None:
    from .agent import parse_user_intent, explain_recommendations

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Set it with: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    print("\nMusic Recommender (AI Mode)")
    print("Describe what you want to listen to. Type 'quit' to exit.\n")

    log = logging.getLogger(__name__)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        try:
            profile = parse_user_intent(user_input)
            print(
                f"\nProfile detected: {profile['favorite_mood']} {profile['favorite_genre']} "
                f"(energy {profile['target_energy']:.2f}, acousticness {profile['target_acousticness']:.2f})"
            )

            recommendations = recommend_songs(profile, songs, k=5)
            _print_recommendations("Your Request", "energy-first", recommendations)

            narrative = explain_recommendations(user_input, recommendations)
            print(f"Curator's note: {narrative}\n")

        except ValueError as exc:
            log.error("Profile parsing failed: %s", exc)
            print("Sorry, I couldn't interpret that. Try describing the mood, energy, or genre you want.\n")
        except Exception as exc:
            log.error("Unexpected error: %s", exc, exc_info=True)
            print("Something went wrong — check logs/recommender.log for details.\n")


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(description="Music Recommender")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Agent mode: describe what you want in plain English (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run reliability evaluation: determinism, score spread, and strategy agreement",
    )
    args = parser.parse_args()

    songs = load_songs("data/songs.csv")

    if args.interactive:
        run_interactive(songs)
    elif args.evaluate:
        from .evaluator import run_full_evaluation
        run_full_evaluation(_PROFILES, songs)
    else:
        run_batch(songs)


if __name__ == "__main__":
    main()
