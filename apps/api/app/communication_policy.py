from __future__ import annotations

from app.communication_schemas import RoutingDecision

HUMAN_REQUIRED_INTENTS = {
    "complaint",
    "refund",
    "financial_commitment",
    "legal_commitment",
    "security_issue",
}


def evaluate_routing(intent: str | None, confidence: int | None) -> RoutingDecision:
    normalized = (intent or "").strip().lower()

    if normalized in HUMAN_REQUIRED_INTENTS:
        return RoutingDecision(
            route="human_required",
            reason=f"intent:{normalized} requires human review",
            confidence=confidence,
            intent=intent,
        )

    if confidence is None:
        return RoutingDecision(
            route="human_required",
            reason="intent confidence is missing",
            confidence=None,
            intent=intent,
        )

    if confidence < 75:
        return RoutingDecision(
            route="human_required",
            reason="intent confidence is below 75",
            confidence=confidence,
            intent=intent,
        )

    return RoutingDecision(
        route="ai_draft",
        reason="low-risk intent with sufficient confidence",
        confidence=confidence,
        intent=intent,
    )
