from __future__ import annotations

import json
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
    Message,
    MessageAuthorType,
    MessageDirection,
)
from app.communication_policy import evaluate_routing
from app.domain import BrandProfile, OutboxEvent, OutboxStatus
from app.engagement_ai import AIUnavailable, classify_intent, draft_reply
from app.engagement_domain import AIDraft, AIDraftStatus, AttributionTouchpoint, OutboundMessage, OutboundStatus
from app.engagement_schemas import AttributionCreate, DraftReviewRequest, OutboundCallback
from app.hardening_domain import ConsentRecord, ConsentStatus, SLATracker, SLAStatus


async def _conversation(session: AsyncSession, workspace_id: uuid.UUID, conversation_id: uuid.UUID) -> Conversation:
    result = await session.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.workspace_id == workspace_id))
    value = result.scalar_one_or_none()
    if not value:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return value


async def _message(session: AsyncSession, workspace_id: uuid.UUID, conversation_id: uuid.UUID, message_id: uuid.UUID) -> Message:
    result = await session.execute(
        select(Message).where(
            Message.id == message_id,
            Message.workspace_id == workspace_id,
            Message.conversation_id == conversation_id,
        )
    )
    value = result.scalar_one_or_none()
    if not value:
        raise HTTPException(status_code=404, detail="Source message not found")
    return value


async def _ensure_support_not_revoked(session: AsyncSession, workspace_id: uuid.UUID, customer_id: uuid.UUID, channel: str) -> None:
    result = await session.execute(select(ConsentRecord).where(
        ConsentRecord.workspace_id == workspace_id,
        ConsentRecord.customer_id == customer_id,
        ConsentRecord.channel == channel,
        ConsentRecord.purpose == "support",
    ))
    record = result.scalar_one_or_none()
    if record is not None and record.status == ConsentStatus.revoked:
        raise HTTPException(status_code=409, detail="Customer revoked support consent on this channel")


async def classify_conversation(session: AsyncSession, workspace_id: uuid.UUID, conversation_id: uuid.UUID, source_message_id: uuid.UUID):
    conversation = await _conversation(session, workspace_id, conversation_id)
    message = await _message(session, workspace_id, conversation_id, source_message_id)
    try:
        intent, confidence, reason = await classify_intent(message.body)
    except AIUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    conversation.intent = intent
    conversation.intent_confidence = confidence
    decision = evaluate_routing(intent, confidence)
    if decision.route == "human_required":
        conversation.status = ConversationStatus.waiting_human
    await session.commit(); await session.refresh(conversation)
    return intent, confidence, reason, decision


async def generate_ai_draft(session: AsyncSession, workspace_id: uuid.UUID, conversation_id: uuid.UUID, source_message_id: uuid.UUID) -> AIDraft:
    conversation = await _conversation(session, workspace_id, conversation_id)
    message = await _message(session, workspace_id, conversation_id, source_message_id)
    decision = evaluate_routing(conversation.intent, conversation.intent_confidence)
    if decision.route != "ai_draft":
        conversation.status = ConversationStatus.waiting_human
        await session.commit()
        raise HTTPException(status_code=409, detail=f"AI draft blocked: {decision.reason}")
    brand_result = await session.execute(select(BrandProfile).where(BrandProfile.workspace_id == workspace_id))
    brand = brand_result.scalar_one_or_none()
    context = ""
    if brand:
        context = f"Brand: {brand.name}; Tone: {brand.tone_of_voice}; Audience: {brand.audience}; Forbidden: {brand.forbidden_terms}"
    try:
        body, model = await draft_reply(customer_message=message.body, intent=conversation.intent or "general_question", brand_context=context)
    except AIUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    draft = AIDraft(workspace_id=workspace_id, conversation_id=conversation_id, source_message_id=source_message_id, intent=conversation.intent or "general_question", confidence=conversation.intent_confidence or 0, model=model, body=body, status=AIDraftStatus.pending)
    session.add(draft)
    await session.commit(); await session.refresh(draft)
    return draft


async def review_ai_draft(session: AsyncSession, workspace_id: uuid.UUID, draft_id: uuid.UUID, reviewer_id: uuid.UUID, payload: DraftReviewRequest) -> tuple[AIDraft, OutboundMessage | None]:
    result = await session.execute(select(AIDraft).where(AIDraft.id == draft_id, AIDraft.workspace_id == workspace_id))
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="AI draft not found")
    if draft.status != AIDraftStatus.pending:
        raise HTTPException(status_code=409, detail="AI draft already reviewed")
    draft.reviewed_by_user_id = reviewer_id
    draft.review_note = payload.note
    if payload.edited_body:
        draft.body = payload.edited_body
    if payload.decision == "rejected":
        draft.status = AIDraftStatus.rejected
        await session.commit(); await session.refresh(draft)
        return draft, None

    conversation = await _conversation(session, workspace_id, draft.conversation_id)
    await _ensure_support_not_revoked(session, workspace_id, conversation.customer_id, conversation.channel)
    draft.status = AIDraftStatus.approved
    idempotency_key = f"ai-draft:{draft.id}"
    existing = await session.execute(select(OutboundMessage).where(OutboundMessage.workspace_id == workspace_id, OutboundMessage.idempotency_key == idempotency_key))
    outbound = existing.scalar_one_or_none()
    if outbound is None:
        outbound = OutboundMessage(workspace_id=workspace_id, conversation_id=conversation.id, customer_id=conversation.customer_id, ai_draft_id=draft.id, channel=conversation.channel, body=draft.body, idempotency_key=idempotency_key, status=OutboundStatus.queued)
        session.add(outbound); await session.flush()
        session.add(OutboxEvent(workspace_id=workspace_id, event_type="message.outbound.requested", aggregate_type="outbound_message", aggregate_id=outbound.id, idempotency_key=f"outbox:{idempotency_key}", payload_json=json.dumps({"outbound_message_id": str(outbound.id), "conversation_id": str(conversation.id), "customer_id": str(conversation.customer_id), "channel": conversation.channel, "body": draft.body, "idempotency_key": idempotency_key, "purpose": "support"}, ensure_ascii=False), status=OutboxStatus.pending))
    await session.commit(); await session.refresh(draft); await session.refresh(outbound)
    return draft, outbound


async def apply_outbound_callback(session: AsyncSession, payload: OutboundCallback) -> OutboundMessage:
    outbound = await session.get(OutboundMessage, payload.outbound_message_id)
    if not outbound:
        raise HTTPException(status_code=404, detail="Outbound message not found")
    if outbound.idempotency_key != payload.idempotency_key:
        raise HTTPException(status_code=409, detail="Outbound idempotency key mismatch")
    desired = OutboundStatus(payload.status)
    if outbound.status in {OutboundStatus.delivered, OutboundStatus.failed, OutboundStatus.cancelled}:
        if outbound.status == desired:
            return outbound
        raise HTTPException(status_code=409, detail="Outbound message already terminal")

    outbound.status = desired
    outbound.external_message_id = payload.external_message_id
    outbound.error_code = payload.error_code
    outbound.error_message = payload.error_message
    now = datetime.now(UTC)
    if desired in {OutboundStatus.sent, OutboundStatus.delivered} and outbound.sent_at is None:
        outbound.sent_at = now
    if desired == OutboundStatus.delivered:
        outbound.delivered_at = now

    if desired in {OutboundStatus.sent, OutboundStatus.delivered}:
        sla_result = await session.execute(select(SLATracker).where(
            SLATracker.workspace_id == outbound.workspace_id,
            SLATracker.conversation_id == outbound.conversation_id,
        ))
        tracker = sla_result.scalar_one_or_none()
        if tracker and tracker.first_responded_at is None:
            tracker.first_responded_at = now
            if tracker.status == SLAStatus.breached:
                tracker.status = SLAStatus.active

    if desired in {OutboundStatus.sent, OutboundStatus.delivered} and payload.external_message_id:
        existing = await session.execute(select(Message).where(Message.workspace_id == outbound.workspace_id, Message.channel == outbound.channel, Message.external_message_id == payload.external_message_id))
        if existing.scalar_one_or_none() is None:
            session.add(Message(workspace_id=outbound.workspace_id, conversation_id=outbound.conversation_id, customer_id=outbound.customer_id, channel=outbound.channel, external_message_id=payload.external_message_id, direction=MessageDirection.outbound, author_type=MessageAuthorType.ai if outbound.ai_draft_id else MessageAuthorType.human, body=outbound.body))
    await session.commit(); await session.refresh(outbound)
    return outbound


async def add_attribution(session: AsyncSession, workspace_id: uuid.UUID, payload: AttributionCreate) -> AttributionTouchpoint:
    customer = await session.get(Customer, payload.customer_id)
    if not customer or customer.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Customer not found")
    touchpoint = AttributionTouchpoint(workspace_id=workspace_id, **payload.model_dump())
    session.add(touchpoint)
    await session.commit(); await session.refresh(touchpoint)
    return touchpoint


async def customer_360(session: AsyncSession, workspace_id: uuid.UUID, customer_id: uuid.UUID) -> dict:
    customer = await session.get(Customer, customer_id)
    if not customer or customer.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Customer not found")
    identities = list((await session.execute(select(CustomerIdentity).where(CustomerIdentity.workspace_id == workspace_id, CustomerIdentity.customer_id == customer_id))).scalars().all())
    conversations = list((await session.execute(select(Conversation).where(Conversation.workspace_id == workspace_id, Conversation.customer_id == customer_id).order_by(Conversation.last_message_at.desc()))).scalars().all())
    leads = list((await session.execute(select(Lead).where(Lead.workspace_id == workspace_id, Lead.customer_id == customer_id))).scalars().all())
    touchpoints = list((await session.execute(select(AttributionTouchpoint).where(AttributionTouchpoint.workspace_id == workspace_id, AttributionTouchpoint.customer_id == customer_id).order_by(AttributionTouchpoint.occurred_at.desc()))).scalars().all())
    lead_ids = [lead.id for lead in leads]
    followups = []
    if lead_ids:
        followups = list((await session.execute(select(FollowUp).where(FollowUp.workspace_id == workspace_id, FollowUp.lead_id.in_(lead_ids), FollowUp.status == FollowUpStatus.pending).order_by(FollowUp.due_at.asc()))).scalars().all())
    return {
        "customer_id": customer.id,
        "display_name": customer.display_name,
        "phone": customer.phone,
        "email": customer.email,
        "identities": [{"channel": x.channel, "external_user_id": x.external_user_id, "username": x.username} for x in identities],
        "conversations": [{"id": str(x.id), "channel": x.channel, "status": x.status.value, "intent": x.intent, "confidence": x.intent_confidence, "last_message_at": x.last_message_at} for x in conversations],
        "leads": [{"id": str(x.id), "status": x.status.value, "score": x.score, "interest": x.interest, "source_channel": x.source_channel} for x in leads],
        "attribution": [{"id": str(x.id), "channel": x.channel, "source": x.source, "campaign": x.campaign, "event_type": x.event_type, "content_id": str(x.content_id) if x.content_id else None, "occurred_at": x.occurred_at} for x in touchpoints],
        "pending_follow_ups": [{"id": str(x.id), "lead_id": str(x.lead_id), "due_at": x.due_at, "reason": x.reason} for x in followups],
    }
