from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.engagement_domain import AIDraftStatus, OutboundStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ClassifyConversationRequest(BaseModel):
    source_message_id: uuid.UUID


class IntentClassificationResult(BaseModel):
    intent: str
    confidence: int
    reason: str
    route: Literal["ai_draft", "human_required"]


class GenerateDraftRequest(BaseModel):
    source_message_id: uuid.UUID


class AIDraftRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: uuid.UUID
    source_message_id: uuid.UUID
    intent: str
    confidence: int
    model: str
    body: str
    status: AIDraftStatus
    reviewed_by_user_id: uuid.UUID | None
    review_note: str
    created_at: datetime


class DraftReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str = Field(default="", max_length=2000)
    edited_body: str | None = Field(default=None, min_length=1, max_length=50000)


class OutboundCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=50000)
    idempotency_key: str = Field(min_length=8, max_length=180)
    purpose: Literal["support", "transactional", "marketing", "sales_followup"] = "support"


class OutboundRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: uuid.UUID
    customer_id: uuid.UUID
    ai_draft_id: uuid.UUID | None
    channel: str
    body: str
    idempotency_key: str
    status: OutboundStatus
    external_message_id: str | None
    error_code: str | None
    error_message: str | None
    sent_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime


class OutboundCallback(BaseModel):
    outbound_message_id: uuid.UUID
    idempotency_key: str
    status: Literal["sent", "delivered", "failed"]
    external_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class AttributionCreate(BaseModel):
    customer_id: uuid.UUID
    lead_id: uuid.UUID | None = None
    content_id: uuid.UUID | None = None
    channel: str = Field(min_length=2, max_length=40)
    source: str = Field(min_length=1, max_length=120)
    campaign: str = Field(default="", max_length=180)
    event_type: str = Field(min_length=2, max_length=80)
    occurred_at: datetime


class AttributionRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    customer_id: uuid.UUID
    lead_id: uuid.UUID | None
    content_id: uuid.UUID | None
    channel: str
    source: str
    campaign: str
    event_type: str
    occurred_at: datetime


class Customer360Read(BaseModel):
    customer_id: uuid.UUID
    display_name: str
    phone: str | None
    email: str | None
    identities: list[dict]
    conversations: list[dict]
    leads: list[dict]
    attribution: list[dict]
    pending_follow_ups: list[dict]
