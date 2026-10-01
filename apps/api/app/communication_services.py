from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_domain import (
    Conversation,
    ConversationStatus,
    Customer,
    CustomerIdentity,
    FollowUp,
    FollowUpStatus,
    Lead,
    LeadStatus,
    Message,
    MessageAuthorType,
    MessageDirection,
)
from app.communication_schemas import (
    FollowUpCreate,
    InboundMessageRequest,
    IntentRequest,
    LeadCreateRequest,
)
from app.domain import Workspace


async def _require_workspace(session: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    workspace = await session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


async def cancel_pending_followups_for_customer(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    customer_id: uuid.UUID,
    reason: str,
) -> int:
    lead_result = await session.execute(
        select(Lead).where(Lead.workspace_id == workspace_id, Lead.customer_id == customer_id)
    )
    lead_ids = [lead.id for lead in lead_result.scalars().all()]
    if not lead_ids:
        return 0
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
    return len(items)


async def ingest_inbound_message(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    payload: InboundMessageRequest,
):
    await _require_workspace(session, workspace_id)

    existing_message = await session.execute(
        select(Message).where(
            Message.workspace_id == workspace_id,
            Message.channel == payload.channel,
            Message.external_message_id == payload.external_message_id,
        )
    )
    message = existing_message.scalar_one_or_none()
    if message:
        conversation = await session.get(Conversation, message.conversation_id)
        customer = await session.get(Customer, message.customer_id)
        if conversation is None or customer is None:
            raise HTTPException(status_code=409, detail="Message references inconsistent state")
        return customer, conversation, message, True

    identity_result = await session.execute(
        select(CustomerIdentity).where(
            CustomerIdentity.workspace_id == workspace_id,
            CustomerIdentity.channel == payload.channel,
            CustomerIdentity.external_user_id == payload.external_user_id,
        )
    )
    identity = identity_result.scalar_one_or_none()

    if identity:
        customer = await session.get(Customer, identity.customer_id)
        if customer is None:
            raise HTTPException(status_code=409, detail="Customer identity is inconsistent")
        if payload.display_name and customer.display_name == "Unknown":
            customer.display_name = payload.display_name
        if payload.phone and not customer.phone:
            customer.phone = payload.phone
        if payload.email and not customer.email:
            customer.email = payload.email
        if payload.username and not identity.username:
            identity.username = payload.username
    else:
        customer = Customer(
            workspace_id=workspace_id,
            display_name=payload.display_name or payload.username or "Unknown",
            phone=payload.phone,
            email=payload.email,
        )
        session.add(customer)
        await session.flush()

        identity = CustomerIdentity(
            workspace_id=workspace_id,
            customer_id=customer.id,
            channel=payload.channel,
            external_user_id=payload.external_user_id,
            username=payload.username,
        )
        session.add(identity)

    conversation_result = await session.execute(
        select(Conversation)
        .where(
            Conversation.workspace_id == workspace_id,
            Conversation.customer_id == customer.id,
            Conversation.channel == payload.channel,
            Conversation.status.in_([ConversationStatus.open, ConversationStatus.waiting_human]),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    conversation = conversation_result.scalar_one_or_none()
    if conversation is None:
        conversation = Conversation(
            workspace_id=workspace_id,
            customer_id=customer.id,
            channel=payload.channel,
        )
        session.add(conversation)
        await session.flush()

    message = Message(
        workspace_id=workspace_id,
        conversation_id=conversation.id,
        customer_id=customer.id,
        channel=payload.channel,
        external_message_id=payload.external_message_id,
        direction=MessageDirection.inbound,
        author_type=MessageAuthorType.customer,
        body=payload.body,
    )
    session.add(message)
    conversation.last_message_at = datetime.now(UTC)

    # Business stop condition: a real customer reply pauses/cancels scheduled sales follow-ups.
    await cancel_pending_followups_for_customer(
        session,
        workspace_id,
        customer.id,
        "customer_replied",
    )

    await session.commit()
    await session.refresh(customer)
    await session.refresh(conversation)
    await session.refresh(message)
    return customer, conversation, message, False


async def set_intent(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: IntentRequest,
) -> Conversation:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.intent = payload.intent
    conversation.intent_confidence = payload.confidence
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def handoff_to_human(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    assigned_user_id: uuid.UUID | None,
) -> Conversation:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.status = ConversationStatus.waiting_human
    conversation.assigned_user_id = assigned_user_id
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def create_or_update_lead(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: LeadCreateRequest,
) -> Lead:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await session.execute(
        select(Lead).where(
            Lead.workspace_id == workspace_id,
            Lead.customer_id == conversation.customer_id,
        )
    )
    lead = result.scalar_one_or_none()

    if lead is None:
        lead = Lead(
            workspace_id=workspace_id,
            customer_id=conversation.customer_id,
            source_channel=conversation.channel,
            score=payload.score,
            owner_user_id=payload.owner_user_id,
            interest=payload.interest,
        )
        session.add(lead)
    else:
        lead.score = max(lead.score, payload.score)
        if payload.owner_user_id:
            lead.owner_user_id = payload.owner_user_id
        if payload.interest:
            lead.interest = payload.interest

    if lead.score >= 70 and lead.status == LeadStatus.new:
        lead.status = LeadStatus.qualified

    await session.commit()
    await session.refresh(lead)
    return lead


async def create_follow_up(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    lead_id: uuid.UUID,
    payload: FollowUpCreate,
) -> FollowUp:
    result = await session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.workspace_id == workspace_id)
    )
    lead = result.scalar_one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status in {LeadStatus.won, LeadStatus.lost}:
        raise HTTPException(status_code=409, detail="Closed lead cannot receive a new follow-up")

    follow_up = FollowUp(
        workspace_id=workspace_id,
        lead_id=lead_id,
        due_at=payload.due_at,
        reason=payload.reason,
        assigned_user_id=payload.assigned_user_id,
    )
    session.add(follow_up)
    await session.commit()
    await session.refresh(follow_up)
    return follow_up
