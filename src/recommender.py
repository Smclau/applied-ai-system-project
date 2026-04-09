from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        """Initialize the Recommender with a catalog of Song objects."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k songs from the catalog for the given user profile."""
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-English explanation of why a song was recommended to a user."""
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    import csv
    songs = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["energy"]        = float(row["energy"])
            row["tempo_bpm"]     = float(row["tempo_bpm"])
            row["valence"]       = float(row["valence"])
            row["danceability"]  = float(row["danceability"])
            row["acousticness"]  = float(row["acousticness"])
            songs.append(row)
    return songs

# Each mood mapped to (energy, valence) coordinates for proximity scoring
MOOD_COORDINATES: Dict[str, Tuple[float, float]] = {
    "happy":    (0.75, 0.85),
    "energetic":(0.88, 0.72),
    "intense":  (0.90, 0.50),
    "angry":    (0.92, 0.35),
    "focused":  (0.42, 0.55),
    "chill":    (0.38, 0.62),
    "relaxed":  (0.36, 0.70),
    "dreamy":   (0.55, 0.68),
    "moody":    (0.65, 0.40),
    "sad":      (0.28, 0.28),
}

def _mood_proximity(mood_a: str, mood_b: str) -> float:
    """Return a 0–1 score for how similar two moods are using their 2D coordinates."""
    e1, v1 = MOOD_COORDINATES.get(mood_a, (0.5, 0.5))
    e2, v2 = MOOD_COORDINATES.get(mood_b, (0.5, 0.5))
    distance = ((e1 - e2) ** 2 + (v1 - v2) ** 2) ** 0.5
    max_distance = 2 ** 0.5  # max possible distance in a 1x1 space
    return round(1 - (distance / max_distance), 4)

def _score_song(song: Dict, user_prefs: Dict) -> Tuple[float, str]:
    """Score a single song against the user profile. Returns (score, explanation)."""
    # Derive target_valence from mood coordinates so it's always consistent
    target_valence = MOOD_COORDINATES.get(user_prefs["favorite_mood"], (0.5, 0.6))[1]

    energy_score  = 1 - abs(song["energy"]      - user_prefs["target_energy"])
    valence_score = 1 - abs(song["valence"]      - target_valence)
    acoustic_score= 1 - abs(song["acousticness"] - user_prefs["target_acousticness"])
    mood_score    = _mood_proximity(song["mood"], user_prefs["favorite_mood"])
    genre_bonus   = 1.0 if song["genre"] == user_prefs["favorite_genre"] else 0.0

    # Note: a near-perfect energy match can outweigh a mood mismatch between
    # close neighbors (e.g. "chill" vs "focused"). Acceptable for this simulation.
    score = (energy_score   * 0.35
           + valence_score  * 0.25
           + mood_score     * 0.20
           + acoustic_score * 0.05
           + genre_bonus    * 0.15)

    reasons = []
    if genre_bonus:
        reasons.append(f"{song['genre']} genre match")
    if mood_score == 1.0:
        reasons.append(f"{song['mood']} mood match")
    elif mood_score >= 0.80:
        reasons.append(f"{song['mood']} mood close to {user_prefs['favorite_mood']}")
    if energy_score >= 0.90:
        reasons.append(f"energy {song['energy']} ≈ your {user_prefs['target_energy']}")
    explanation = ", ".join(reasons) if reasons else "closest attribute match"
    return round(score, 4), explanation

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored = [(_score_song(song, user_prefs), song) for song in songs]
    scored.sort(key=lambda x: x[0][0], reverse=True)
    return [(song, score, explanation) for (score, explanation), song in scored[:k]]
