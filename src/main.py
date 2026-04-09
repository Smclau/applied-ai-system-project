"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    profiles = {
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
    }

    for profile_name, user_prefs in profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)
        print(f"\n=== {profile_name} ===\n")
        for song, score, explanation in recommendations:
            print(f"{song['title']} - Score: {score:.2f}")
            print(f"Because: {explanation}")
            print()


if __name__ == "__main__":
    main()
