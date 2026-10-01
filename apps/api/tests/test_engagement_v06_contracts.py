import uuid

import pytest
from pydantic import ValidationError

from app.communication_policy import evaluate_routing
from app.engagement_ai import AIUnavailable, classify_intent
from app.engagement_domain import AIDraftStatus, OutboundStatus
from app.engagement_schemas import DraftReviewRequest, OutboundCallback
from app.outbox_worker import webhook_for_event
from app.settings import settings


def test_sensitive_intent_requires_human() -> None:
    decision = evaluate_routing("refund", 99)
    assert decision.route == "human_required"


def test_low_confidence_requires_human() -> None:
    decision = evaluate_routing("price_request", 60)
    assert decision.route == "human_required"


def test_safe_high_confidence_allows_ai_draft() -> None:
    decision = evaluate_routing("price_request", 90)
    assert decision.route == "ai_draft"


def test_ai_draft_status_contract() -> None:
    assert {item.value for item in AIDraftStatus} == {"pending", "approved", "rejected"}


def test_outbound_status_contract() -> None:
    assert {item.value for item in OutboundStatus} == {
        "queued",
        "sent",
        "delivered",
        "failed",
        "cancelled",
    }


def test_review_decision_is_bounded() -> None:
    assert DraftReviewRequest(decision="approved").decision == "approved"
    with pytest.raises(ValidationError):
        DraftReviewRequest(decision="send_anyway")


def test_outbound_callback_requires_supported_state() -> None:
    data = {
        "outbound_message_id": uuid.uuid4(),
        "idempotency_key": "12345678",
        "status": "sent",
    }
    assert OutboundCallback(**data).status == "sent"
    data["status"] = "unknown"
    with pytest.raises(ValidationError):
        OutboundCallback(**data)


def test_worker_routes_outbound_event_to_outbound_webhook() -> None:
    assert webhook_for_event("message.outbound.requested") == settings.n8n_outbound_webhook_url
    assert webhook_for_event("content.publish.requested") == settings.n8n_publish_webhook_url


@pytest.mark.asyncio
async def test_unconfigured_ai_fails_closed() -> None:
    if settings.ai_api_base_url or settings.ai_api_key or settings.ai_model:
        pytest.skip("AI provider is configured in this environment")
    with pytest.raises(AIUnavailable):
        await classify_intent("قیمت چقدره؟")
