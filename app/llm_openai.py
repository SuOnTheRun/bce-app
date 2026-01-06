import os
from typing import Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def _client() -> OpenAI:
    # OpenAI SDK reads OPENAI_API_KEY from env automatically,
    # but we also validate it's present to fail clearly.
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=key)


def generate_structured(
    *,
    model: str,
    system_instruction: str,
    user_prompt: str,
    response_model: Type[T],
) -> T:
    """
    Pass A: Structured output parsed into a Pydantic model.
    """
    client = _client()

    resp = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
        text_format=response_model,
    )

    return resp.output_parsed


def generate_text(
    *,
    model: str,
    system_instruction: str,
    user_prompt: str,
) -> str:
    """
    Pass B: Normal text generation.
    """
    client = _client()

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
    )

    return (resp.output_text or "").strip()
