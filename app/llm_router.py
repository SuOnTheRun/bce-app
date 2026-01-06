import os
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

def provider() -> str:
    return (os.getenv("LLM_PROVIDER") or "offline").strip().lower()

def generate_structured(*, model: str, system_instruction: str, user_prompt: str, response_model: Type[T]) -> T:
    p = provider()
    if p == "offline":
        from app.llm_offline import generate_structured_offline
        return generate_structured_offline(response_model=response_model)

    # Keep for later if you regain access
    if p == "openai":
        from app.llm_openai import generate_structured as openai_structured
        return openai_structured(
            model=model,
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            response_model=response_model,
        )

    if p == "gemini":
        from app.llm_gemini import generate_structured_json
        schema = response_model.model_json_schema()
        data = generate_structured_json(
            model=model,
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            response_schema=schema,
        )
        return response_model.model_validate(data)

    raise RuntimeError(f"Unknown LLM_PROVIDER: {p}")

def generate_text(*, model: str, system_instruction: str, user_prompt: str, decision_map_json: str) -> str:
    p = provider()
    if p == "offline":
        from app.llm_offline import generate_text_offline
        return generate_text_offline(decision_map_json=decision_map_json)

    if p == "openai":
        from app.llm_openai import generate_text as openai_text
        return openai_text(model=model, system_instruction=system_instruction, user_prompt=user_prompt)

    if p == "gemini":
        from app.llm_gemini import generate_text as gemini_text
        return gemini_text(model=model, system_instruction=system_instruction, user_prompt=user_prompt)

    raise RuntimeError(f"Unknown LLM_PROVIDER: {p}")
