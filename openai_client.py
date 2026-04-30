"""
Wrapper kolem OpenAI API pro generování textů na bannery.

Volá Chat Completions API s vynuceným JSON schema výstupem.
Pro reasoning modely (gpt-5.x, o-series) předává navíc reasoning_effort.
"""

import json
import os
from typing import Any

from openai import OpenAI

from prompt import OUTPUT_SCHEMA, SYSTEM_PROMPT, build_user_message


# Modely dostupné v dropdownu UI.
# První v seznamu = default.
AVAILABLE_MODELS = [
    "gpt-5.5",                # default — nejvyšší kvalita (reasoning)
    "gpt-5.4",                # alternativa — reasoning
    "gpt-5.3-chat-latest",    # rychlý non-reasoning model
]

REASONING_EFFORT_OPTIONS = ["low", "medium", "high"]
DEFAULT_REASONING_EFFORT = "medium"


def _supports_reasoning_effort(model: str) -> bool:
    """Reasoning modely (gpt-5.x, o-series) podporují parametr reasoning_effort."""
    model_lower = model.lower()
    if "chat" in model_lower:
        return False
    return (
        model_lower.startswith("gpt-5")
        or model_lower.startswith("o1")
        or model_lower.startswith("o3")
        or model_lower.startswith("o4")
    )


def _get_client() -> OpenAI:
    """Vytvoří OpenAI klienta. API klíč čte z env proměnné OPENAI_API_KEY."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Chybí OPENAI_API_KEY. Zkontroluj soubor .env ve složce s aplikací."
        )
    return OpenAI(api_key=api_key)


def generate_variants(
    job_title: str,
    job_description: str,
    model: str = "gpt-5.5",
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
) -> dict[str, Any]:
    """
    Vygeneruje 4 varianty bullet-textů pro banner k dané pozici.

    Vrací:
        {
            "varianty": [
                {"bullet_1": "...", "bullet_2": "...", "bullet_3": "...", "bullet_4": "..."},
                ... 4x
            ],
            "_meta": {
                "model": "...",
                "reasoning_effort": "...",
                "input_tokens": int,
                "output_tokens": int,
            }
        }
    """
    if not job_title.strip():
        raise ValueError("Název pozice nesmí být prázdný.")
    if not job_description.strip():
        raise ValueError("Popis pozice nesmí být prázdný.")

    client = _get_client()
    user_message = build_user_message(job_title, job_description)

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "banner_variants",
                "strict": True,
                "schema": OUTPUT_SCHEMA,
            },
        },
    }

    # reasoning_effort předáváme jen modelům, které ho podporují
    if _supports_reasoning_effort(model) and reasoning_effort:
        kwargs["reasoning_effort"] = reasoning_effort

    response = client.chat.completions.create(**kwargs)

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise RuntimeError("Model vrátil prázdnou odpověď.")

    parsed = json.loads(raw_content)

    # Doplníme metadata pro UI a historii
    usage = response.usage
    parsed["_meta"] = {
        "model": model,
        "reasoning_effort": reasoning_effort if _supports_reasoning_effort(model) else None,
        "input_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": usage.completion_tokens if usage else None,
    }

    return parsed
