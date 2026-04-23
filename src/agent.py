"""
Claude-powered agent layer for the music recommender.

Responsibilities:
  1. parse_user_intent  — convert free-text input into a structured user profile
  2. explain_recommendations — narrate why the scored results fit the user's request

Both calls use ephemeral prompt caching on the system message so repeated
interactive queries only pay the token cost once per 5-minute cache window.
"""

import json
import logging
import os
from typing import List, Tuple, Dict

from anthropic import Anthropic

logger = logging.getLogger(__name__)

_client = Anthropic()  # reads ANTHROPIC_API_KEY from environment

_VALID_GENRES = {
    "lofi", "pop", "rock", "jazz", "electronic", "folk",
    "classical", "ambient", "r&b", "hip-hop", "metal", "synthwave", "indie pop",
}
_VALID_MOODS = {
    "happy", "energetic", "intense", "angry", "focused",
    "chill", "relaxed", "dreamy", "moody", "sad",
}

_PARSE_SYSTEM = (
    "You are a music profile extractor. Given a description of what a user wants to listen to, "
    "return ONLY valid JSON with exactly these four keys:\n"
    "  favorite_genre   — one of: lofi, pop, rock, jazz, electronic, folk, classical, ambient, r&b, hip-hop, metal, synthwave, indie pop\n"
    "  favorite_mood    — one of: happy, energetic, intense, angry, focused, chill, relaxed, dreamy, moody, sad\n"
    "  target_energy    — float 0.0–1.0 (0=very calm, 1=very intense)\n"
    "  target_acousticness — float 0.0–1.0 (0=electronic/produced, 1=fully acoustic)\n"
    "No explanation, no markdown, no extra keys. Only the JSON object."
)

_EXPLAIN_SYSTEM = (
    "You are a friendly music curator. Given what a user asked for and a ranked list of "
    "recommended songs, write 2–3 sentences explaining why these tracks fit their vibe. "
    "Be specific — mention genre, mood, or energy details. Do not list the songs again."
)


def parse_user_intent(user_input: str) -> Dict:
    """Call Claude to convert a natural-language request into a structured user profile dict."""
    logger.info("Parsing intent | input=%r", user_input)

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=[{"type": "text", "text": _PARSE_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_input}],
    )

    raw = response.content[0].text.strip()
    logger.debug("Claude parse response: %s", raw)

    try:
        profile = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Claude JSON: %s | raw=%r", exc, raw)
        raise ValueError(f"Claude returned non-JSON: {raw!r}") from exc

    _validate_profile(profile)
    logger.info("Parsed profile: %s", profile)
    return profile


def explain_recommendations(user_input: str, recommendations: List[Tuple[Dict, float, str]]) -> str:
    """Call Claude to generate a narrative explanation for a set of scored recommendations."""
    songs_text = "\n".join(
        f"{i + 1}. \"{song['title']}\" by {song['artist']} "
        f"({song['genre']}, {song['mood']}, energy={song['energy']}, score={score:.2f}) — {explanation}"
        for i, (song, score, explanation) in enumerate(recommendations)
    )

    logger.info("Requesting explanation for %d recommendations", len(recommendations))

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=[{"type": "text", "text": _EXPLAIN_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": f"User asked for: {user_input}\n\nTop recommendations:\n{songs_text}",
        }],
    )

    explanation = response.content[0].text.strip()
    logger.debug("Claude explanation: %s", explanation)
    return explanation


def _validate_profile(profile: Dict) -> None:
    required = ("favorite_genre", "favorite_mood", "target_energy", "target_acousticness")
    for field in required:
        if field not in profile:
            raise ValueError(f"Missing required field in Claude response: {field!r}")

    if profile["favorite_genre"] not in _VALID_GENRES:
        logger.warning("Unexpected genre %r — using as-is", profile["favorite_genre"])
    if profile["favorite_mood"] not in _VALID_MOODS:
        logger.warning("Unexpected mood %r — using as-is", profile["favorite_mood"])

    try:
        profile["target_energy"] = float(profile["target_energy"])
        profile["target_acousticness"] = float(profile["target_acousticness"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Energy/acousticness must be floats: {exc}") from exc

    profile["target_energy"] = max(0.0, min(1.0, profile["target_energy"]))
    profile["target_acousticness"] = max(0.0, min(1.0, profile["target_acousticness"]))
