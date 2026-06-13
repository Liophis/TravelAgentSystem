from typing import Any

import httpx

from app.core.config import settings


class LLMClientError(RuntimeError):
    pass


def chat_completion_text(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    timeout_seconds: float | None = None,
) -> str:
    if not settings.llm_api_key:
        raise LLMClientError("LLM_API_KEY is not configured.")

    base_url = settings.llm_base_url.rstrip("/")
    payload: dict[str, Any] = {
        "model": model or settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=timeout_seconds or settings.llm_timeout_seconds) as client:
            response = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise LLMClientError(f"LLM provider request failed: {exc}") from exc

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMClientError("LLM provider returned an invalid response shape.") from exc
    if not isinstance(content, str) or not content.strip():
        raise LLMClientError("LLM provider returned empty content.")
    return content
