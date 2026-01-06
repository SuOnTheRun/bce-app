import os
import json
from typing import Any, Dict

from google import genai
from google.genai import types


def _gemini_client() -> genai.Client:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=key)


def _strip_json_fences(text: str) -> str:
    # Defensive: some models may wrap JSON in ```json ... ```
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.endswith("```"):
            t = t.rsplit("```", 1)[0]
    return t.strip()


def generate_structured_json(
    *,
    model: str,
    system_instruction: str,
    user_prompt: str,
    response_schema: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pass A: Uses Gemini structured outputs (JSON schema) to return JSON.
    """
    client = _gemini_client()

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.2,
    )

    resp = client.models.generate_content(
        model=model,
        contents=[user_prompt],
        config=config,
    )

    # The SDK returns text; parse to dict
    raw = _strip_json_fences(resp.text)
    return json.loads(raw)


def generate_text(
    *,
    model: str,
    system_instruction: str,
    user_prompt: str,
) -> str:
    """
    Pass B: Normal text generation.
    """
    client = _gemini_client()

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.6,
    )

    resp = client.models.generate_content(
        model=model,
        contents=[user_prompt],
        config=config,
    )
    return (resp.text or "").strip()
