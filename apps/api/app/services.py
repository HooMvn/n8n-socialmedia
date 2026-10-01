from __future__ import annotations

import json
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import (
    Approval,
    BrandProfile,
    ContentItem,
    ContentStatus,
    OutboxEvent,
    OutboxStatus,
    Publication,
    PublicationStatus,
    Workspace,
)
from app.schemas import BrandUpsert, ContentCreate, DecisionRequest, PublicationCallback, PublishRequest


async def require_workspace(session: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    workspace = await session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


async def get_content_for_workspace(
    session: AsyncSession, workspace_id: uuid.UUID, content_id: uuid.UUID
) -> ContentItem:
    result = await session.execute(
        select(ContentItem).where(
            ContentItem.id == content_id,
            ContentItem.workspace_id == workspace_id,
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found in workspace")
    return content


async def upsert_brand(
    session: AsyncSession, workspace_id: uuid.UUID, payload: BrandUpsert
) -> BrandProfile:
    await require_workspace(session, workspace_id)
    result = await session.execute(select(BrandProfile).where(BrandProfile.workspace_id == workspace_id))
    brand = result.scalar_one_or_none()
    if brand is None:
        brand = BrandProfile(workspace_id=workspace_id, **payload.model_dump())
        session.add(brand)
    else:
        for field, value in payload.model_dump().items():
            setattr(brand, field, value)
    await session.commit()
    await session.refresh(brand)
    return brand


async def create_content(
    session: AsyncSession, workspace_id: uuid.UUID, payload: ContentCreate
) -> ContentItem:
    await require_workspace(session, workspace_id)
    brand_result = await session.execute(
        select(BrandProfile).where(
            BrandProfile.id == payload.brand_id,
            BrandProfile.workspace_id == workspace_id,
        )
    )
    if brand_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Brand not found in workspace")

    content = ContentItem(workspace_id=workspace_id, **payload.model_dump())
    session.add(content)
    await session.commit()
    await session.refresh(content)
    return content


async def transition_content(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    content_id: uuid.UUID,
    target: ContentStatus,
    decision: DecisionRequest | None = None,
) -> ContentItem:
    content = await get_content_for_workspace(session, workspace_id, content_id)
    allowed: dict[ContentStatus, set[ContentStatus]] = {
        ContentStatus.draft: {ContentStatus.in_review},
        ContentStatus.in_review: {ContentStatus.approved, ContentStatus.rejected},
        ContentStatus.rejected: {ContentStatus.in_review},
    }
    if target not in allowed.get(content.status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid transition: {content.status.value} -> {target.value}",
        )

    content.status = target
    if target in {ContentStatus.approved, ContentStatus.rejected}:
        if decision is None:
            raise HTTPException(status_code=422, detail="Decision metadata is required")
        session.add(
            Approval(
                workspace_id=workspace_id,
                content_id=content.id,
                decision=target.value,
                actor=decision.actor,
                note=decision.note,
            )
        )
    await session.commit()
    await session.refresh(content)
    return content


async def request_publication(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    content_id: uuid.UUID,
    payload: PublishRequest,
) -> Publication:
    content = await get_content_for_workspace(session, workspace_id, content_id)
    existing_result = await session.execute(
        select(Publication).where(Publication.idempotency_key == payload.idempotency_key)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        if existing.workspace_id != workspace_id or existing.content_id != content_id:
            raise HTTPException(status_code=409, detail="Idempotency key already used for another request")
        return existing

    if content.status not in {ContentStatus.approved, ContentStatus.failed}:
        raise HTTPException(status_code=409, detail="Only approved or failed content can be published")

    publication = Publication(
        workspace_id=workspace_id,
        content_id=content.id,
        platform=content.platform,
        idempotency_key=payload.idempotency_key,
        status=PublicationStatus.pending,
    )
    session.add(publication)
    await session.flush()

    event_payload = {
        "event_type": "content.publish.requested",
        "workspace_id": str(workspace_id),
        "publication_id": str(publication.id),
        "content_id": str(content.id),
        "platform": content.platform,
        "text": content.body,
        "idempotency_key": payload.idempotency_key,
    }
    session.add(
        OutboxEvent(
            workspace_id=workspace_id,
            event_type="content.publish.requested",
            aggregate_type="publication",
            aggregate_id=publication.id,
            idempotency_key=f"outbox:{payload.idempotency_key}",
            payload_json=json.dumps(event_payload, ensure_ascii=False),
            status=OutboxStatus.pending,
        )
    )
    content.status = ContentStatus.publish_requested
    await session.commit()
    await session.refresh(publication)
    return publication


async def apply_publication_callback(
    session: AsyncSession, payload: PublicationCallback
) -> Publication:
    publication = await session.get(Publication, payload.publication_id)
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    if publication.idempotency_key != payload.idempotency_key:
        raise HTTPException(status_code=409, detail="Idempotency key does not match publication")

    # Idempotent replay of the exact terminal result is safe.
    desired = PublicationStatus(payload.status)
    if publication.status == desired:
        return publication
    if publication.status in {PublicationStatus.published, PublicationStatus.failed}:
        raise HTTPException(status_code=409, detail="Publication is already terminal")

    content = await session.get(ContentItem, publication.content_id)
    publication.status = desired
    publication.external_id = payload.external_id
    publication.external_url = payload.external_url
    publication.error_code = payload.error_code
    publication.error_message = payload.error_message
    if content:
        content.status = ContentStatus.published if desired == PublicationStatus.published else ContentStatus.failed
    await session.commit()
    await session.refresh(publication)
    return publication
