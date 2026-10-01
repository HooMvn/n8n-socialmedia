from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_roles, require_workspace_member
from app.database import get_session
from app.domain import (
    BrandProfile,
    ContentStatus,
    Membership,
    OutboxEvent,
    OutboxStatus,
    Publication,
    User,
    Workspace,
    WorkspaceRole,
)
from app.schemas import (
    BrandRead,
    BrandUpsert,
    ContentCreate,
    ContentRead,
    DecisionRequest,
    OutboxAck,
    OutboxEventRead,
    PublicationCallback,
    PublicationRead,
    PublishRequest,
    WorkspaceCreate,
    WorkspaceRead,
)
from app.services import (
    apply_publication_callback,
    create_content,
    get_content_for_workspace,
    request_publication,
    transition_content,
    upsert_brand,
)
from app.settings import settings

router = APIRouter(prefix="/api/v1")
EDIT_ROLES = (WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.editor)
REVIEW_ROLES = (WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)


@router.post("/workspaces", response_model=WorkspaceRead, status_code=201)
async def create_workspace(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    duplicate = await session.execute(select(Workspace).where(Workspace.slug == payload.slug))
    if duplicate.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Workspace slug already exists")
    workspace = Workspace(**payload.model_dump())
    session.add(workspace)
    await session.flush()
    session.add(Membership(workspace_id=workspace.id, user_id=current_user.id, role=WorkspaceRole.owner))
    await session.commit()
    await session.refresh(workspace)
    return workspace


@router.put("/workspaces/{workspace_id}/brand", response_model=BrandRead)
async def set_brand(
    workspace_id: uuid.UUID,
    payload: BrandUpsert,
    _: Membership = Depends(require_roles(*EDIT_ROLES)),
    session: AsyncSession = Depends(get_session),
):
    return await upsert_brand(session, workspace_id, payload)


@router.get("/workspaces/{workspace_id}/brand", response_model=BrandRead)
async def get_brand(
    workspace_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(BrandProfile).where(BrandProfile.workspace_id == workspace_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.post("/workspaces/{workspace_id}/contents", response_model=ContentRead, status_code=201)
async def add_content(
    workspace_id: uuid.UUID,
    payload: ContentCreate,
    _: Membership = Depends(require_roles(*EDIT_ROLES)),
    session: AsyncSession = Depends(get_session),
):
    return await create_content(session, workspace_id, payload)


@router.get("/workspaces/{workspace_id}/contents/{content_id}", response_model=ContentRead)
async def get_content(
    workspace_id: uuid.UUID,
    content_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    return await get_content_for_workspace(session, workspace_id, content_id)


@router.post("/workspaces/{workspace_id}/contents/{content_id}/submit-review", response_model=ContentRead)
async def submit_review(
    workspace_id: uuid.UUID,
    content_id: uuid.UUID,
    _: Membership = Depends(require_roles(*EDIT_ROLES)),
    session: AsyncSession = Depends(get_session),
):
    return await transition_content(session, workspace_id, content_id, ContentStatus.in_review)


@router.post("/workspaces/{workspace_id}/contents/{content_id}/approve", response_model=ContentRead)
async def approve_content(
    workspace_id: uuid.UUID,
    content_id: uuid.UUID,
    payload: DecisionRequest,
    _: Membership = Depends(require_roles(*REVIEW_ROLES)),
    session: AsyncSession = Depends(get_session),
):
    return await transition_content(
        session, workspace_id, content_id, ContentStatus.approved, decision=payload
    )


@router.post("/workspaces/{workspace_id}/contents/{content_id}/reject", response_model=ContentRead)
async def reject_content(
    workspace_id: uuid.UUID,
    content_id: uuid.UUID,
    payload: DecisionRequest,
    _: Membership = Depends(require_roles(*REVIEW_ROLES)),
    session: AsyncSession = Depends(get_session),
):
    return await transition_content(
        session, workspace_id, content_id, ContentStatus.rejected, decision=payload
    )


@router.post("/workspaces/{workspace_id}/contents/{content_id}/publish", response_model=PublicationRead)
async def publish_content(
    workspace_id: uuid.UUID,
    content_id: uuid.UUID,
    payload: PublishRequest,
    _: Membership = Depends(require_roles(*REVIEW_ROLES)),
    session: AsyncSession = Depends(get_session),
):
    return await request_publication(session, workspace_id, content_id, payload)


@router.get(
    "/workspaces/{workspace_id}/publications/{publication_id}", response_model=PublicationRead
)
async def get_publication(
    workspace_id: uuid.UUID,
    publication_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Publication).where(
            Publication.id == publication_id,
            Publication.workspace_id == workspace_id,
        )
    )
    publication = result.scalar_one_or_none()
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found in workspace")
    return publication


def _verify_automation_secret(value: str | None) -> None:
    if not value or value != settings.n8n_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid automation secret")


@router.get("/automation/outbox", response_model=list[OutboxEventRead])
async def pending_outbox(
    limit: int = 20,
    x_automation_secret: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    _verify_automation_secret(x_automation_secret)
    safe_limit = max(1, min(limit, 100))
    result = await session.execute(
        select(OutboxEvent)
        .where(OutboxEvent.status == OutboxStatus.pending)
        .order_by(OutboxEvent.created_at.asc())
        .limit(safe_limit)
    )
    return list(result.scalars().all())


@router.post("/automation/outbox/ack")
async def ack_outbox(
    payload: OutboxAck,
    x_automation_secret: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    _verify_automation_secret(x_automation_secret)
    event = await session.get(OutboxEvent, payload.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Outbox event not found")
    event.status = OutboxStatus.delivered if payload.delivered else OutboxStatus.failed
    await session.commit()
    return {"status": event.status.value}


@router.post("/publications/callback", response_model=PublicationRead)
async def publication_callback(
    payload: PublicationCallback,
    x_automation_secret: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    _verify_automation_secret(x_automation_secret)
    return await apply_publication_callback(session, payload)
