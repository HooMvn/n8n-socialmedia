from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_roles, require_workspace_member
from app.communication_domain import (
    Conversation,
    ConversationStatus,
    Customer,
    FollowUp,
    FollowUpStatus,
    Lead,
    LeadStatus,
    Message,
)
from app.communication_policy import evaluate_routing
from app.communication_schemas import (
    ConversationRead,
    ConversationStatusUpdate,
    CustomerRead,
    FollowUpCreate,
    FollowUpRead,
    FollowUpStatusUpdate,
    HandoffRequest,
    InboundMessageRequest,
    InboundMessageResult,
    IntentRequest,
    LeadCreateRequest,
    LeadRead,
    LeadStatusUpdate,
    MessageRead,
    RoutingDecision,
)
from app.communication_services import (
    create_follow_up,
    create_or_update_lead,
    handoff_to_human,
    ingest_inbound_message,
    set_intent,
)
from app.database import get_session
from app.domain import Membership, WorkspaceRole
from app.settings import settings

router = APIRouter(prefix="/api/v1", tags=["communication"])


def _verify_automation_secret(value: str | None) -> None:
    if not value or value != settings.n8n_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid automation secret",
        )


@router.post(
    "/automation/workspaces/{workspace_id}/inbound",
    response_model=InboundMessageResult,
)
async def ingest_channel_message(
    workspace_id: uuid.UUID,
    payload: InboundMessageRequest,
    x_automation_secret: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    _verify_automation_secret(x_automation_secret)
    customer, conversation, message, duplicate = await ingest_inbound_message(
        session,
        workspace_id,
        payload,
    )
    return InboundMessageResult(
        customer=customer,
        conversation=conversation,
        message=message,
        duplicate=duplicate,
    )


@router.get("/workspaces/{workspace_id}/inbox", response_model=list[ConversationRead])
async def inbox(
    workspace_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conversation)
        .where(Conversation.workspace_id == workspace_id)
        .order_by(Conversation.last_message_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.get(
    "/workspaces/{workspace_id}/conversations/{conversation_id}/messages",
    response_model=list[MessageRead],
)
async def conversation_messages(
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Message)
        .where(
            Message.workspace_id == workspace_id,
            Message.conversation_id == conversation_id,
        )
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


@router.patch(
    "/workspaces/{workspace_id}/conversations/{conversation_id}",
    response_model=ConversationRead,
)
async def update_conversation_status(
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: ConversationStatusUpdate,
    _: Membership = Depends(
        require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)
    ),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation.status = ConversationStatus(payload.status)
    await session.commit()
    await session.refresh(conversation)
    return conversation


@router.post(
    "/workspaces/{workspace_id}/conversations/{conversation_id}/intent",
    response_model=ConversationRead,
)
async def classify_intent(
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: IntentRequest,
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
    return await set_intent(session, workspace_id, conversation_id, payload)


@router.get(
    "/workspaces/{workspace_id}/conversations/{conversation_id}/routing",
    response_model=RoutingDecision,
)
async def routing_decision(
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return evaluate_routing(conversation.intent, conversation.intent_confidence)


@router.post(
    "/workspaces/{workspace_id}/conversations/{conversation_id}/handoff",
    response_model=ConversationRead,
)
async def human_handoff(
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: HandoffRequest,
    _: Membership = Depends(
        require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)
    ),
    session: AsyncSession = Depends(get_session),
):
    return await handoff_to_human(
        session,
        workspace_id,
        conversation_id,
        payload.assigned_user_id,
    )


@router.post(
    "/workspaces/{workspace_id}/conversations/{conversation_id}/lead",
    response_model=LeadRead,
)
async def create_lead_from_conversation(
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: LeadCreateRequest,
    _: Membership = Depends(
        require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)
    ),
    session: AsyncSession = Depends(get_session),
):
    return await create_or_update_lead(session, workspace_id, conversation_id, payload)


@router.get("/workspaces/{workspace_id}/leads", response_model=list[LeadRead])
async def list_leads(
    workspace_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Lead)
        .where(Lead.workspace_id == workspace_id)
        .order_by(Lead.updated_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.patch("/workspaces/{workspace_id}/leads/{lead_id}", response_model=LeadRead)
async def update_lead(
    workspace_id: uuid.UUID,
    lead_id: uuid.UUID,
    payload: LeadStatusUpdate,
    _: Membership = Depends(
        require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)
    ),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.workspace_id == workspace_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = LeadStatus(payload.status)
    if payload.score is not None:
        lead.score = payload.score
    await session.commit()
    await session.refresh(lead)
    return lead


@router.post(
    "/workspaces/{workspace_id}/leads/{lead_id}/follow-ups",
    response_model=FollowUpRead,
    status_code=201,
)
async def add_follow_up(
    workspace_id: uuid.UUID,
    lead_id: uuid.UUID,
    payload: FollowUpCreate,
    _: Membership = Depends(
        require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)
    ),
    session: AsyncSession = Depends(get_session),
):
    return await create_follow_up(session, workspace_id, lead_id, payload)


@router.get(
    "/workspaces/{workspace_id}/follow-ups",
    response_model=list[FollowUpRead],
)
async def list_follow_ups(
    workspace_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(FollowUp)
        .where(FollowUp.workspace_id == workspace_id)
        .order_by(FollowUp.due_at.asc())
        .limit(200)
    )
    return list(result.scalars().all())


@router.patch(
    "/workspaces/{workspace_id}/follow-ups/{follow_up_id}",
    response_model=FollowUpRead,
)
async def update_follow_up(
    workspace_id: uuid.UUID,
    follow_up_id: uuid.UUID,
    payload: FollowUpStatusUpdate,
    _: Membership = Depends(
        require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)
    ),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(FollowUp).where(
            FollowUp.id == follow_up_id,
            FollowUp.workspace_id == workspace_id,
        )
    )
    follow_up = result.scalar_one_or_none()
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    follow_up.status = FollowUpStatus(payload.status)
    await session.commit()
    await session.refresh(follow_up)
    return follow_up


@router.get(
    "/workspaces/{workspace_id}/customers/{customer_id}",
    response_model=CustomerRead,
)
async def get_customer(
    workspace_id: uuid.UUID,
    customer_id: uuid.UUID,
    _: Membership = Depends(require_workspace_member),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.workspace_id == workspace_id,
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
