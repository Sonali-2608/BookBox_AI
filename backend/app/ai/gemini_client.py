"""
Thin wrapper around the Gemini API (google-genai SDK). This is the only
module that touches the SDK directly — everything else calls
generate_content() / generate_json(), which keeps AI features easy to
test (mock this module) and easy to re-point at a different model via
the GEMINI_MODEL setting without touching call sites.
"""

import json
from typing import Optional

from app.config import settings

_client = None


class GeminiError(Exception):
    """Raised when Gemini isn't configured, can't be reached, errors, or
    returns something we can't use. Callers should treat this as a
    signal to degrade gracefully — never to fabricate a response."""


def _get_client():
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise GeminiError("GEMINI_API_KEY is not configured on the server")
        from google import genai

        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def generate_content(prompt: str, system_instruction: Optional[str] = None) -> str:
    """Calls Gemini and returns the plain text response."""
    client = _get_client()
    try:
        from google.genai import types

        config = (
            types.GenerateContentConfig(system_instruction=system_instruction)
            if system_instruction
            else None
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
    except GeminiError:
        raise
    except Exception as exc:
        # The SDK can raise several different exception types for auth,
        # network, rate-limit, and invalid-model errors — we don't rely
        # on any specific one and just treat all of them as a Gemini
        # failure the caller should degrade gracefully from.
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    text = getattr(response, "text", None)
    if not text:
        raise GeminiError("Gemini returned an empty response")
    return text


def generate_json(prompt: str, system_instruction: Optional[str] = None) -> dict:
    """Calls Gemini asking for JSON output and parses it. Raises
    GeminiError (rather than returning something malformed) if the
    response isn't valid JSON, so callers know to fall back rather than
    show a broken or hallucinated result."""
    text = generate_content(prompt, system_instruction=system_instruction)
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise GeminiError(f"Gemini did not return valid JSON: {exc}") from exc
