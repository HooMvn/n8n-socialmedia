from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.communication_domain import (
    ConversationStatus,
    FollowUpStatus,
    LeadStatus,
    MessageAuthorType,
    MessageDirection,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class InboundMessageRequest(BaseModel):
    channel: str = Field(min_length=2, max_length=40)
    external_user_id: str = Field(min_length=1, max_length=255)
    external_message_id: str = Field(min_length=1, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=320)
    body: str = Field(min_length=1, max_length=50000)


class CustomerRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    display_name: str
    phone: str | None
    email: str | None
    created_at: datetime


class ConversationRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    customer_id: uuid.UUID
    channel: str
    status: ConversationStatus
    assigned_user_id: uuid.UUID | None
    intent: str | None
    intent_confidence: int | None
    last_message_at: datetime


class ConversationStatusUpdate(BaseModel):
    status: Literal["open", "waiting_human", "resolved", "closed"]


class MessageRead(ORMModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    customer_id: uuid.UUID
    channel: str
    external_message_id: str
    direction: MessageDirection
    author_type: MessageAuthorType
    body: str
    created_at: datetime


class InboundMessageResult(BaseModel):
    customer: CustomerRead
    conversation: ConversationRead
    message: MessageRead
    duplicate: bool = False


class IntentRequest(BaseModel):
    intent: str = Field(min_length=2, max_length=80)
    confidence: int = Field(ge=0, le=100)


class RoutingDecision(BaseModel):
    route: Literal["ai_draft", "human_required"]
    reason: str
    confidence: int | None = None
    intent: str | None = None


class HandoffRequest(BaseModel):
    assigned_user_id: uuid.UUID | None = None
    reason: str = Field(default="", max_length=500)


class LeadCreateRequest(BaseModel):
    interest: str = Field(default="", max_length=255)
    score: int = Field(default=0, ge=0, le=100)
    owner_user_id: uuid.UUID | None = None


class LeadRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    customer_id: uuid.UUID
    source_channel: str
    status: LeadStatus
    score: int
    owner_user_id: uuid.UUID | None
    interest: str
    created_at: datetime


class LeadStatusUpdate(BaseModel):
    status: Literal["new", "qualified", "contacted", "proposal", "won", "lost"]
    score: int | None = Field(default=None, ge=0, le=100)


class FollowUpCreate(BaseModel):
    due_at: datetime
    reason: str = Field(default="", max_length=255)
    assigned_user_id: uuid.UUID | None = None


class FollowUpRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    lead_id: uuid.UUID
    due_at: datetime
    status: FollowUpStatus
    reason: str
    assigned_user_id: uuid.UUID | None
    created_at: datetime


class FollowUpStatusUpdate(BaseModel):
    status: Literal["pending", "done", "cancelled"]
