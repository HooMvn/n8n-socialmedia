from __future__ import annotations

import json
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_domain import Conversation
from app.domain import OutboxEvent, OutboxStatus
from app.engagement_domain import OutboundMessage, OutboundStatus
from app.engagement_schemas import OutboundCreateRequest
from app.hardening_domain import ConsentRecord, ConsentStatus


async def _enforce_consent(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    customer_id: uuid.UUID,
    channel: str,
    purpose: str,
) -> None:
    result = await session.execute(
        select(ConsentRecord).where(
            ConsentRecord.workspace_id == workspace_id,
            ConsentRecord.customer_id == customer_id,
            ConsentRecord.channel == channel,
            ConsentRecord.purpose == purpose,
        )
    )
    record = result.scalar_one_or_none()
    if purpose in {"marketing", "sales_followup"}:
        if record is None or record.status != ConsentStatus.granted:
            raise HTTPException(status_code=409, detail=f"Consent required for {purpose}")
    elif record is not None and record.status == ConsentStatus.revoked:
        raise HTTPException(status_code=409, detail=f"Customer revoked {purpose} consent on {channel}")


async def queue_human_outbound(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: OutboundCreateRequest,
) -> OutboundMessage:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await _enforce_consent(
        session,
        workspace_id,
        conversation.customer_id,
        conversation.channel,
        payload.purpose,
    )

    existing_result = await session.execute(
        select(OutboundMessage).where(
            OutboundMessage.workspace_id == workspace_id,
            OutboundMessage.idempotency_key == payload.idempotency_key,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        if existing.conversation_id != conversation_id:
            raise HTTPException(status_code=409, detail="Idempotency key belongs to another conversation")
        return existing

    outbound = OutboundMessage(
        workspace_id=workspace_id,
        conversation_id=conversation.id,
        customer_id=conversation.customer_id,
        ai_draft_id=None,
        channel=conversation.channel,
        body=payload.body,
        idempotency_key=payload.idempotency_key,
        status=OutboundStatus.queued,
    )
    session.add(outbound)
    await session.flush()
    session.add(
        OutboxEvent(
            workspace_id=workspace_id,
            event_type="message.outbound.requested",
            aggregate_type="outbound_message",
            aggregate_id=outbound.id,
            idempotency_key=f"outbox:{payload.idempotency_key}",
            payload_json=json.dumps(
                {
                    "outbound_message_id": str(outbound.id),
                    "conversation_id": str(conversation.id),
                    "customer_id": str(conversation.customer_id),
                    "channel": conversation.channel,
                    "body": payload.body,
                    "idempotency_key": payload.idempotency_key,
                    "author_type": "human",
                    "purpose": payload.purpose,
                },
                ensure_ascii=False,
            ),
            status=OutboxStatus.pending,
        )
    )
    await session.commit()
    await session.refresh(outbound)
    return outbound
