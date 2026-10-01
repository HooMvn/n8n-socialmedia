from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_roles, require_workspace_member
from app.communication_domain import CustomerIdentity, FollowUp, FollowUpStatus, Lead
from app.database import get_session
from app.domain import Membership, User, WorkspaceRole
from app.engagement_domain import AIDraft, AIDraftStatus, OutboundMessage
from app.engagement_schemas import (
    AIDraftRead,
    AttributionCreate,
    AttributionRead,
    ClassifyConversationRequest,
    Customer360Read,
    DraftReviewRequest,
    GenerateDraftRequest,
    IntentClassificationResult,
    OutboundCallback,
    OutboundCreateRequest,
    OutboundRead,
)
from app.engagement_services import (
    add_attribution,
    apply_outbound_callback,
    classify_conversation,
    customer_360,
    generate_ai_draft,
    review_ai_draft,
)
from app.outbound_services import queue_human_outbound
from app.settings import settings

router = APIRouter(prefix="/api/v1", tags=["engagement-v0.6"])


def _verify_automation_secret(value: str | None) -> None:
    if not value or value != settings.n8n_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid automation secret")


@router.post(
    "/workspaces/{workspace_id}/conversations/{conversation_id}/ai/classify",
    response_model=IntentClassificationResult,
)
async def ai_classify(
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: ClassifyConversationRequest,
    _: Membership = Depends(
        require_roles(
            WorkspaceRole.owner,
            WorkspaceRole.admin,
            WorkspaceRole.editor,
            WorkspaceRole.reviewer,
        )
    ),
    session: AsyncSession = Depends(get_session),
):
    intent, confidence, reason, decision = await classify_conversation(
        session, workspace_id, conversation_id, payload.source_message_id
    )
    return IntentClassificationResult(
        intent=intent,
        confidence=confidence,
        reason=reason,
        route=decision.route,
    )


@router.post(
    "/workspaces/{workspace_id}/conversations/{conversation_id}/ai/drafts",
    response_model=AIDraftRead,
    status_code=201,
)
async def create_ai_draft(
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: GenerateDraftRequest,
    _: Membership = Depends(
        require_roles(
            WorkspaceRole.owner,
            WorkspaceRole.admin,
            WorkspaceRole.editor,
            WorkspaceRole.reviewer,
        )
    ),
    session: AsyncSession = Depends(get_session),
):
    return await generate_ai_draft(session, workspace_id, conversation_id, payload.source_message_id)


@router.get("/workspaces/{workspace_id}/ai/drafts", response_model=list[AIDraftRead])
async def list_pending_drafts(
    workspace_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(AIDraft)
        .where(AIDraft.workspace_id == workspace_id, AIDraft.status == AIDraftStatus.pending)
        .order_by(AIDraft.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.post("/workspaces/{workspace_id}/ai/drafts/{draft_id}/review")
async def review_draft(
    workspace_id: uuid.UUID,
    draft_id: uuid.UUID,
    payload: DraftReviewRequest,
    current_user: User = Depends(get_current_user),
    _: Membership = Depends(
        require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)
    ),
    session: AsyncSession = Depends(get_session),
):
    draft, outbound = await review_ai_draft(
        session, workspace_id, draft_id, current_user.id, payload
    )
    return {
        "draft": AIDraftRead.model_validate(draft),
        "outbound": OutboundRead.model_validate(outbound) if outbound else None,
    }


@router.post(
    "/workspaces/{workspace_id}/conversations/{conversation_id}/outbound",
    response_model=OutboundRead,
    status_code=201,
)
async def create_human_outbound(
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: OutboundCreateRequest,
    _: Membership = Depends(
        require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.editor, WorkspaceRole.reviewer)
    ),
    session: AsyncSession = Depends(get_session),
):
    return await queue_human_outbound(session, workspace_id, conversation_id, payload)


@router.get("/workspaces/{workspace_id}/outbound", response_model=list[OutboundRead])
async def list_outbound(
    workspace_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(OutboundMessage)
        .where(OutboundMessage.workspace_id == workspace_id)
        .order_by(OutboundMessage.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.get("/automation/outbound/{outbound_id}/delivery-context")
async def outbound_delivery_context(
    outbound_id: uuid.UUID,
    x_automation_secret: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    _verify_automation_secret(x_automation_secret)
    outbound = await session.get(OutboundMessage, outbound_id)
    if not outbound:
        raise HTTPException(status_code=404, detail="Outbound message not found")
    result = await session.execute(
        select(CustomerIdentity).where(
            CustomerIdentity.workspace_id == outbound.workspace_id,
            CustomerIdentity.customer_id == outbound.customer_id,
            CustomerIdentity.channel == outbound.channel,
        )
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=409, detail="No delivery identity for outbound channel")
    return {
        "outbound_message_id": str(outbound.id),
        "workspace_id": str(outbound.workspace_id),
        "conversation_id": str(outbound.conversation_id),
        "channel": outbound.channel,
        "target_external_user_id": identity.external_user_id,
        "body": outbound.body,
        "idempotency_key": outbound.idempotency_key,
    }


@router.post("/automation/outbound/callback", response_model=OutboundRead)
async def outbound_callback(
    payload: OutboundCallback,
    x_automation_secret: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    _verify_automation_secret(x_automation_secret)
    return await apply_outbound_callback(session, payload)


@router.post(
    "/workspaces/{workspace_id}/attribution",
    response_model=AttributionRead,
    status_code=201,
)
async def create_attribution(
    workspace_id: uuid.UUID,
    payload: AttributionCreate,
    _: Membership = Depends(
        require_roles(
            WorkspaceRole.owner,
            WorkspaceRole.admin,
            WorkspaceRole.editor,
            WorkspaceRole.reviewer,
        )
    ),
    session: AsyncSession = Depends(get_session),
):
    return await add_attribution(session, workspace_id, payload)


@router.get(
    "/workspaces/{workspace_id}/customers/{customer_id}/360",
    response_model=Customer360Read,
)
async def get_customer_360(
    workspace_id: uuid.UUID,
    customer_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    return await customer_360(session, workspace_id, customer_id)


@router.post("/workspaces/{workspace_id}/customers/{customer_id}/follow-ups/stop")
async def stop_customer_followups(
    workspace_id: uuid.UUID,
    customer_id: uuid.UUID,
    reason: str = "manual_stop",
    _: Membership = Depends(
        require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)
    ),
    session: AsyncSession = Depends(get_session),
):
    lead_result = await session.execute(
        select(Lead).where(Lead.workspace_id == workspace_id, Lead.customer_id == customer_id)
    )
    lead_ids = [lead.id for lead in lead_result.scalars().all()]
    if not lead_ids:
        return {"cancelled": 0, "reason": reason}
    result = await session.execute(
        select(FollowUp).where(
            FollowUp.workspace_id == workspace_id,
            FollowUp.lead_id.in_(lead_ids),
            FollowUp.status == FollowUpStatus.pending,
        )
    )
    items = list(result.scalars().all())
    for item in items:
        item.status = FollowUpStatus.cancelled
        item.reason = f"{item.reason} | stopped:{reason}"[:255]
    await session.commit()
    return {"cancelled": len(items), "reason": reason}
