from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.communication_domain import (
    ConversationStatus,
    FollowUpStatus,
    LeadStatus,
    MessageAuthorType,
    MessageDirection,
)
from app.communication_policy import evaluate_routing
from app.communication_schemas import (
    FollowUpCreate,
    InboundMessageRequest,
    IntentRequest,
    LeadCreateRequest,
)


def test_communication_state_contracts() -> None:
    assert {status.value for status in ConversationStatus} == {
        "open",
        "waiting_human",
        "resolved",
        "closed",
    }
    assert {direction.value for direction in MessageDirection} == {"inbound", "outbound"}
    assert {author.value for author in MessageAuthorType} == {
        "customer",
        "ai",
        "human",
        "system",
    }
    assert {status.value for status in LeadStatus} == {
        "new",
        "qualified",
        "contacted",
        "proposal",
        "won",
        "lost",
    }
    assert {status.value for status in FollowUpStatus} == {"pending", "done", "cancelled"}


def test_inbound_message_contract_requires_stable_external_ids() -> None:
    payload = InboundMessageRequest(
        channel="telegram",
        external_user_id="123",
        external_message_id="456",
        body="قیمت چقدره؟",
    )
    assert payload.channel == "telegram"
    assert payload.external_message_id == "456"


def test_empty_inbound_body_is_rejected() -> None:
    with pytest.raises(ValidationError):
        InboundMessageRequest(
            channel="telegram",
            external_user_id="123",
            external_message_id="456",
            body="",
        )


def test_intent_confidence_is_bounded() -> None:
    assert IntentRequest(intent="sales_interest", confidence=90).confidence == 90
    with pytest.raises(ValidationError):
        IntentRequest(intent="sales_interest", confidence=101)


def test_lead_score_is_bounded() -> None:
    assert LeadCreateRequest(score=70).score == 70
    with pytest.raises(ValidationError):
        LeadCreateRequest(score=-1)


def test_follow_up_contract_accepts_timezone_aware_datetime() -> None:
    due_at = datetime.now(UTC)
    payload = FollowUpCreate(due_at=due_at, reason="پیگیری درخواست قیمت")
    assert payload.due_at == due_at
    assert payload.reason == "پیگیری درخواست قیمت"


def test_routing_policy_requires_human_for_sensitive_intent() -> None:
    decision = evaluate_routing("complaint", 99)
    assert decision.route == "human_required"


def test_routing_policy_requires_human_for_low_confidence() -> None:
    decision = evaluate_routing("pricing", 60)
    assert decision.route == "human_required"


def test_routing_policy_allows_ai_draft_for_low_risk_high_confidence() -> None:
    decision = evaluate_routing("pricing", 90)
    assert decision.route == "ai_draft"
