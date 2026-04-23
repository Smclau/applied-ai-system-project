import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

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
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "target_acousticness": 0.75 if user.likes_acoustic else 0.25,
        }
        song_dicts = [asdict(s) for s in self.songs]
        results = recommend_songs(user_prefs, song_dicts, k=k)
        ids = {s["id"] for s, _, _ in results}
        return [s for s in self.songs if s.id in ids]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-English explanation of why a song was recommended to a user."""
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "target_acousticness": 0.75 if user.likes_acoustic else 0.25,
        }
        _, explanation = _score_song(asdict(song), user_prefs)
        return explanation

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
    logger.info("Loaded %d songs from %s", len(songs), csv_path)
    return songs

# Genres that earn partial credit (0.5) when they don't exactly match the user's genre
GENRE_NEIGHBORS: Dict[str, list] = {
    "lofi":       ["ambient", "jazz", "classical"],
    "ambient":    ["lofi", "classical", "folk"],
    "jazz":       ["lofi", "classical", "r&b"],
    "classical":  ["lofi", "ambient", "jazz", "folk"],
    "folk":       ["classical", "ambient", "jazz"],
    "rock":       ["metal", "electronic", "synthwave"],
    "metal":      ["rock", "electronic"],
    "electronic": ["synthwave", "rock", "metal"],
    "synthwave":  ["electronic", "rock"],
    "pop":        ["indie pop", "r&b", "synthwave"],
    "indie pop":  ["pop", "folk", "r&b"],
    "r&b":        ["pop", "indie pop", "jazz"],
    "hip-hop":    ["r&b", "pop", "electronic"],
}

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
    # Infer target danceability from energy — high-energy users prefer danceable tracks
    target_dance   = user_prefs["target_energy"]
    dance_score    = 1 - abs(song["danceability"] - target_dance)
    user_genre = user_prefs["favorite_genre"]
    if song["genre"] == user_genre:
        genre_bonus = 1.0
    elif song["genre"] in GENRE_NEIGHBORS.get(user_genre, []):
        genre_bonus = 0.5
    else:
        genre_bonus = 0.0

    # Weights sum: 0.50 + 0.20 + 0.15 + 0.05 + 0.04 + 0.06 = 1.00
    score = (energy_score   * 0.50
           + valence_score  * 0.20
           + mood_score     * 0.15
           + dance_score    * 0.05
           + acoustic_score * 0.04
           + genre_bonus    * 0.06)

    reasons = []
    if genre_bonus == 1.0:
        reasons.append(f"{song['genre']} genre match")
    elif genre_bonus == 0.5:
        reasons.append(f"{song['genre']} close to {user_genre}")
    if mood_score == 1.0:
        reasons.append(f"{song['mood']} mood match")
    elif mood_score >= 0.80:
        reasons.append(f"{song['mood']} mood close to {user_prefs['favorite_mood']}")
    if energy_score >= 0.90:
        reasons.append(f"energy {song['energy']} ≈ your {user_prefs['target_energy']}")
    explanation = ", ".join(reasons) if reasons else "closest attribute match"
    return round(score, 4), explanation

def _score_genre_first(song: Dict, user_prefs: Dict) -> Tuple[float, str]:
    """Genre-First strategy: genre match weighted at 45%, energy/mood secondary."""
    target_valence = MOOD_COORDINATES.get(user_prefs["favorite_mood"], (0.5, 0.6))[1]
    user_genre = user_prefs["favorite_genre"]
    if song["genre"] == user_genre:
        genre_bonus = 1.0
    elif song["genre"] in GENRE_NEIGHBORS.get(user_genre, []):
        genre_bonus = 0.5
    else:
        genre_bonus = 0.0

    energy_score  = 1 - abs(song["energy"]      - user_prefs["target_energy"])
    valence_score = 1 - abs(song["valence"]      - target_valence)
    mood_score    = _mood_proximity(song["mood"], user_prefs["favorite_mood"])
    acoustic_score= 1 - abs(song["acousticness"] - user_prefs["target_acousticness"])
    dance_score   = 1 - abs(song["danceability"] - user_prefs["target_energy"])

    # Weights sum: 0.45 + 0.25 + 0.15 + 0.10 + 0.03 + 0.02 = 1.00
    score = (genre_bonus   * 0.45
           + energy_score  * 0.25
           + mood_score    * 0.15
           + valence_score * 0.10
           + acoustic_score* 0.03
           + dance_score   * 0.02)

    reasons = []
    if genre_bonus == 1.0:
        reasons.append(f"{song['genre']} genre match")
    elif genre_bonus == 0.5:
        reasons.append(f"{song['genre']} close to {user_genre}")
    if mood_score >= 0.80:
        reasons.append(f"{song['mood']} mood")
    if energy_score >= 0.90:
        reasons.append(f"energy {song['energy']} ≈ your {user_prefs['target_energy']}")
    explanation = ", ".join(reasons) if reasons else "closest attribute match"
    return round(score, 4), explanation


def _score_mood_first(song: Dict, user_prefs: Dict) -> Tuple[float, str]:
    """Mood-First strategy: mood proximity weighted at 45%, genre is minor."""
    target_valence = MOOD_COORDINATES.get(user_prefs["favorite_mood"], (0.5, 0.6))[1]
    user_genre = user_prefs["favorite_genre"]
    if song["genre"] == user_genre:
        genre_bonus = 1.0
    elif song["genre"] in GENRE_NEIGHBORS.get(user_genre, []):
        genre_bonus = 0.5
    else:
        genre_bonus = 0.0

    energy_score  = 1 - abs(song["energy"]      - user_prefs["target_energy"])
    valence_score = 1 - abs(song["valence"]      - target_valence)
    mood_score    = _mood_proximity(song["mood"], user_prefs["favorite_mood"])
    acoustic_score= 1 - abs(song["acousticness"] - user_prefs["target_acousticness"])
    dance_score   = 1 - abs(song["danceability"] - user_prefs["target_energy"])

    # Weights sum: 0.45 + 0.25 + 0.15 + 0.10 + 0.03 + 0.02 = 1.00
    score = (mood_score    * 0.45
           + valence_score * 0.25
           + energy_score  * 0.15
           + genre_bonus   * 0.10
           + acoustic_score* 0.03
           + dance_score   * 0.02)

    reasons = []
    if mood_score == 1.0:
        reasons.append(f"{song['mood']} mood match")
    elif mood_score >= 0.80:
        reasons.append(f"{song['mood']} mood close to {user_prefs['favorite_mood']}")
    if genre_bonus == 1.0:
        reasons.append(f"{song['genre']} genre")
    elif genre_bonus == 0.5:
        reasons.append(f"{song['genre']} close to {user_genre}")
    explanation = ", ".join(reasons) if reasons else "closest attribute match"
    return round(score, 4), explanation


STRATEGIES: Dict[str, object] = {
    "energy-first": _score_song,
    "genre-first":  _score_genre_first,
    "mood-first":   _score_mood_first,
}


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, strategy: str = "energy-first") -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    logger.debug(
        "recommend_songs | strategy=%s k=%d genre=%s mood=%s energy=%.2f",
        strategy, k,
        user_prefs.get("favorite_genre"), user_prefs.get("favorite_mood"),
        user_prefs.get("target_energy", 0),
    )
    scorer = STRATEGIES.get(strategy, _score_song)
    scored = [(scorer(song, user_prefs), song) for song in songs]
    scored.sort(key=lambda x: x[0][0], reverse=True)

    # Diversity re-ranking: greedily pick songs, penalizing genre+mood clusters
    # already represented in the selected results.
    selected = []
    seen_clusters = {}  # (genre, mood) -> count of times already picked
    DIVERSITY_PENALTY = 0.15  # score penalty per repeat of the same cluster

    for (score, explanation), song in scored:
        cluster = (song["genre"], song["mood"])
        penalty = seen_clusters.get(cluster, 0) * DIVERSITY_PENALTY
        adjusted_score = round(score - penalty, 4)
        selected.append((song, adjusted_score, explanation))
        seen_clusters[cluster] = seen_clusters.get(cluster, 0) + 1

    selected.sort(key=lambda x: x[1], reverse=True)
    top = selected[:k]
    logger.info(
        "Top %d results | #1: %r (%.4f)",
        len(top), top[0][0].get("title") if top else None, top[0][1] if top else 0,
    )
    return top
