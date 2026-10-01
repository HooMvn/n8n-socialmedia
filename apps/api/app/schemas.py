from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain import ContentStatus, PublicationStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$")


class WorkspaceRead(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime


class BrandUpsert(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    tone_of_voice: str = Field(default="", max_length=5000)
    audience: str = Field(default="", max_length=5000)
    forbidden_terms: str = Field(default="", max_length=5000)


class BrandRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    tone_of_voice: str
    audience: str
    forbidden_terms: str
    updated_at: datetime


class ContentCreate(BaseModel):
    brand_id: uuid.UUID
    title: str = Field(min_length=2, max_length=180)
    body: str = Field(min_length=1, max_length=50000)
    platform: str = Field(min_length=2, max_length=40)


class ContentRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    brand_id: uuid.UUID
    title: str
    body: str
    platform: str
    status: ContentStatus
    created_at: datetime
    updated_at: datetime


class DecisionRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=120)
    note: str = Field(default="", max_length=5000)


class PublishRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=180)


class PublicationRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    content_id: uuid.UUID
    platform: str
    idempotency_key: str
    status: PublicationStatus
    external_id: str | None
    external_url: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class PublicationCallback(BaseModel):
    publication_id: uuid.UUID
    idempotency_key: str
    status: Literal["published", "failed"]
    external_id: str | None = None
    external_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class OutboxEventRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    event_type: str
    aggregate_type: str
    aggregate_id: uuid.UUID
    idempotency_key: str
    payload_json: str
    created_at: datetime


class OutboxAck(BaseModel):
    event_id: uuid.UUID
    delivered: bool
    error_message: str | None = None
