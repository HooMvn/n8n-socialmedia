from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.hardening_domain import ConsentStatus, IdentityVerificationStatus, SLAStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class KnowledgeSourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    source_type: Literal["manual", "faq", "website", "product", "policy", "document"]
    source_uri: str = Field(default="", max_length=1000)
    text: str = Field(min_length=1, max_length=200000)


class KnowledgeSourceRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    source_type: str
    source_uri: str
    status: str
    created_at: datetime


class RetrievalHit(BaseModel):
    chunk_id: uuid.UUID
    source_id: uuid.UUID
    title: str
    body: str
    score: int


class GroundedDraftRequest(BaseModel):
    source_message_id: uuid.UUID
    max_chunks: int = Field(default=5, ge=1, le=10)


class ConsentUpsert(BaseModel):
    purpose: Literal["support", "transactional", "marketing", "sales_followup"]
    channel: str = Field(min_length=2, max_length=40)
    status: Literal["granted", "revoked", "unknown"]
    evidence: str = Field(default="", max_length=5000)


class ConsentRead(ORMModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    purpose: str
    channel: str
    status: ConsentStatus
    evidence: str
    effective_at: datetime


class SLAStart(BaseModel):
    first_response_minutes: int = Field(default=30, ge=1, le=10080)
    resolution_minutes: int | None = Field(default=1440, ge=1, le=43200)


class SLARead(ORMModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    status: SLAStatus
    first_response_due_at: datetime
    resolution_due_at: datetime | None
    first_responded_at: datetime | None
    breached_at: datetime | None
    escalation_level: int


class IdentityVerifyRequest(BaseModel):
    verification_method: Literal["phone_otp", "email_link", "provider_verified", "manual"]
    verified_value: str = Field(min_length=2, max_length=500)


class IdentityVerificationRead(ORMModel):
    identity_id: uuid.UUID
    status: IdentityVerificationStatus
    verification_method: str
    verified_at: datetime | None


class IdentityMergeRequest(BaseModel):
    source_customer_id: uuid.UUID
    target_customer_id: uuid.UUID
    verified_identity_ids: list[uuid.UUID] = Field(min_length=1)


class ProviderCredentialCreate(BaseModel):
    provider: Literal["telegram", "instagram", "whatsapp"]
    credential_name: str = Field(min_length=2, max_length=100)
    secret: str = Field(min_length=8, max_length=10000)


class ProviderCredentialRead(BaseModel):
    id: uuid.UUID
    provider: str
    credential_name: str
    status: str
    last_verified_at: datetime | None


class AttributionSummary(BaseModel):
    total_touchpoints: int
    by_channel: dict[str, int]
    by_source: dict[str, int]
    by_event_type: dict[str, int]
