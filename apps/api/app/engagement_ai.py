from __future__ import annotations

import json

import httpx
from fastapi import HTTPException

from app.settings import settings


INTENTS = [
    "general_question",
    "price_request",
    "sales_interest",
    "support",
    "complaint",
    "refund",
    "financial_commitment",
    "legal_commitment",
    "security_issue",
    "spam",
]


class AIUnavailable(RuntimeError):
    pass


def _require_ai_config() -> None:
    if not settings.ai_api_base_url or not settings.ai_api_key or not settings.ai_model:
        raise AIUnavailable("AI provider is not configured")


async def _chat(messages: list[dict[str, str]], *, temperature: float = 0.1) -> str:
    _require_ai_config()
    url = f"{settings.ai_api_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.ai_model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {settings.ai_api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        response = await client.post(url, json=payload, headers=headers)
    if response.status_code >= 400:
        raise AIUnavailable(f"AI provider returned HTTP {response.status_code}")
    try:
        return response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIUnavailable("AI provider response shape is invalid") from exc


async def classify_intent(message: str) -> tuple[str, int, str]:
    prompt = (
        "You classify customer-service messages. Return JSON only with keys intent, confidence, reason. "
        f"intent must be one of: {', '.join(INTENTS)}. confidence is integer 0..100. "
        "Never invent customer facts. If ambiguous, lower confidence."
    )
    raw = await _chat([
        {"role": "system", "content": prompt},
        {"role": "user", "content": message},
    ])
    try:
        data = json.loads(raw)
        intent = str(data["intent"]).strip().lower()
        confidence = int(data["confidence"])
        reason = str(data.get("reason", ""))[:1000]
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise AIUnavailable("AI classifier returned invalid JSON") from exc
    if intent not in INTENTS or not 0 <= confidence <= 100:
        raise AIUnavailable("AI classifier returned out-of-contract values")
    return intent, confidence, reason


async def draft_reply(*, customer_message: str, intent: str, brand_context: str = "") -> tuple[str, str]:
    system = (
        "Draft a concise customer reply in Persian. Return JSON only with key body. "
        "Do not promise refunds, discounts, legal commitments, financial guarantees, delivery dates, or policy exceptions. "
        "Do not claim information that is not in the supplied brand context. If required information is missing, ask a short clarifying question."
    )
    raw = await _chat([
        {"role": "system", "content": system},
        {"role": "user", "content": f"Intent: {intent}\nBrand context: {brand_context}\nCustomer: {customer_message}"},
    ], temperature=0.3)
    try:
        body = str(json.loads(raw)["body"]).strip()
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise AIUnavailable("AI drafter returned invalid JSON") from exc
    if not body:
        raise AIUnavailable("AI drafter returned empty text")
    return body, settings.ai_model


def ai_http_exception(exc: AIUnavailable) -> HTTPException:
    return HTTPException(status_code=503, detail=str(exc))
