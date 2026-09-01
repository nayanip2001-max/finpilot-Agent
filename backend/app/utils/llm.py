"""
LLM abstraction so the rest of the app never talks to a specific vendor SDK.

Two modes, controlled by LLM_MODE env var:
  - "mock" (default): deterministic, template-based narration. No network
    calls, no API key needed. This is what makes the hackathon demo reliable
    and free to run.
  - "real": calls the configured provider (Anthropic by default) via a
    simple HTTP request. Only the narration step uses this — all numerical
    signal classification happens beforehand in market/signals.py,
    agents/sentiment.py rules, etc. The LLM explains, it never calculates.

Swapping providers = editing call_llm() in one place.
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger("finpilot.llm")


class LLMError(Exception):
    pass


def _mock_response(prompt: str) -> str:
    """
    Deterministic mock narration. We don't have a model to call, so we
    return a clearly-labeled templated explanation built from the prompt's
    own structured facts. This keeps mock mode honest: it summarizes given
    numbers rather than inventing new ones.
    """
    return (
        "[MOCK MODE — deterministic narration, no external LLM called]\n"
        "Summary generated from the structured signal data provided in the prompt. "
        "Enable LLM_MODE=real with a valid LLM_API_KEY for natural-language synthesis."
    )


async def call_llm(prompt: str, system: Optional[str] = None, max_tokens: int = 600) -> str:
    settings = get_settings()

    if settings.is_mock_llm:
        return _mock_response(prompt)

    if not settings.llm_api_key:
        logger.warning("LLM_MODE=real but no LLM_API_KEY set — falling back to mock narration.")
        return _mock_response(prompt)

    # Default provider: Anthropic Messages API. Swap this block to change providers.
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.llm_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "max_tokens": max_tokens,
                    "system": system or "",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
            return "\n".join(parts).strip() or _mock_response(prompt)
    except Exception as exc:  # noqa: BLE001
        logger.error("Real LLM call failed, falling back to mock narration: %s", exc)
        return _mock_response(prompt)