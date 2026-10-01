from __future__ import annotations

import base64
import hashlib
import re
import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_domain import Conversation, Customer, CustomerIdentity
from app.engagement_ai import AIUnavailable, draft_reply
from app.engagement_domain import AIDraft, AIDraftStatus, AttributionTouchpoint
from app.hardening_domain import (
    ConsentRecord,
    ConsentStatus,
    IdentityVerification,
    IdentityVerificationStatus,
    KnowledgeChunk,
    KnowledgeSource,
    ProviderCredential,
    SLATracker,
    SLAStatus,
    RetrievalEvidence,
)
from app.hardening_schemas import ConsentUpsert, KnowledgeSourceCreate, ProviderCredentialCreate, SLAStart
from app.settings import settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.app_secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


def _chunks(text: str, size: int = 1200, overlap: int = 180) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    parts: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        parts.append(clean[start:end])
        if end == len(clean):
            break
        start = max(start + 1, end - overlap)
    return parts


def _tokens(value: str) -> Counter[str]:
    return Counter(re.findall(r"[\w\u0600-\u06ff]{2,}", value.lower()))


def lexical_score(query: str, text: str) -> int:
    q = _tokens(query)
    d = _tokens(text)
    if not q:
        return 0
    matched = sum(min(count, d[token]) for token, count in q.items())
    return min(100, round(100 * matched / max(1, sum(q.values()))))


async def create_knowledge_source(session: AsyncSession, workspace_id: uuid.UUID, payload: KnowledgeSourceCreate) -> KnowledgeSource:
    source = KnowledgeSource(workspace_id=workspace_id, name=payload.name, source_type=payload.source_type, source_uri=payload.source_uri)
    session.add(source)
    await session.flush()
    for index, body in enumerate(_chunks(payload.text)):
        checksum = hashlib.sha256(body.encode()).hexdigest()
        session.add(KnowledgeChunk(workspace_id=workspace_id, source_id=source.id, chunk_index=index, title=payload.name, body=body, checksum=checksum))
    await session.commit()
    await session.refresh(source)
    return source


async def retrieve(session: AsyncSession, workspace_id: uuid.UUID, query: str, limit: int = 5) -> list[KnowledgeChunk]:
    result = await session.execute(select(KnowledgeChunk).where(KnowledgeChunk.workspace_id == workspace_id))
    ranked = sorted(result.scalars().all(), key=lambda chunk: lexical_score(query, chunk.body), reverse=True)
    return [chunk for chunk in ranked if lexical_score(query, chunk.body) > 0][:limit]


async def grounded_draft(session: AsyncSession, workspace_id: uuid.UUID, conversation_id: uuid.UUID, source_message_id: uuid.UUID, max_chunks: int) -> AIDraft:
    conversation = await session.get(Conversation, conversation_id)
    if not conversation or conversation.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    from app.communication_domain import Message
    message = await session.get(Message, source_message_id)
    if not message or message.workspace_id != workspace_id or message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Source message not found")
    hits = await retrieve(session, workspace_id, message.body, max_chunks)
    if not hits:
        raise HTTPException(status_code=409, detail="No grounded knowledge found; human review required")
    context = "\n\n".join(f"[SOURCE {i+1}] {chunk.title}: {chunk.body}" for i, chunk in enumerate(hits))
    try:
        body, model = await draft_reply(customer_message=message.body, intent=conversation.intent or "general_question", brand_context=context)
    except AIUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    draft = AIDraft(workspace_id=workspace_id, conversation_id=conversation_id, source_message_id=source_message_id, intent=conversation.intent or "general_question", confidence=conversation.intent_confidence or 0, model=model, body=body, status=AIDraftStatus.pending)
    session.add(draft)
    await session.flush()
    for rank, chunk in enumerate(hits, start=1):
        session.add(RetrievalEvidence(workspace_id=workspace_id, ai_draft_id=draft.id, chunk_id=chunk.id, rank=rank, score=lexical_score(message.body, chunk.body)))
    await session.commit()
    await session.refresh(draft)
    return draft


async def upsert_consent(session: AsyncSession, workspace_id: uuid.UUID, customer_id: uuid.UUID, payload: ConsentUpsert) -> ConsentRecord:
    customer = await session.get(Customer, customer_id)
    if not customer or customer.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Customer not found")
    result = await session.execute(select(ConsentRecord).where(ConsentRecord.workspace_id == workspace_id, ConsentRecord.customer_id == customer_id, ConsentRecord.purpose == payload.purpose, ConsentRecord.channel == payload.channel))
    record = result.scalar_one_or_none()
    if record is None:
        record = ConsentRecord(workspace_id=workspace_id, customer_id=customer_id, purpose=payload.purpose, channel=payload.channel, effective_at=datetime.now(UTC))
        session.add(record)
    record.status = ConsentStatus(payload.status)
    record.evidence = payload.evidence
    record.effective_at = datetime.now(UTC)
    await session.commit(); await session.refresh(record)
    return record


async def start_sla(session: AsyncSession, workspace_id: uuid.UUID, conversation_id: uuid.UUID, payload: SLAStart) -> SLATracker:
    conversation = await session.get(Conversation, conversation_id)
    if not conversation or conversation.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    result = await session.execute(select(SLATracker).where(SLATracker.workspace_id == workspace_id, SLATracker.conversation_id == conversation_id))
    tracker = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if tracker is None:
        tracker = SLATracker(workspace_id=workspace_id, conversation_id=conversation_id, first_response_due_at=now + timedelta(minutes=payload.first_response_minutes))
        session.add(tracker)
    tracker.first_response_due_at = now + timedelta(minutes=payload.first_response_minutes)
    tracker.resolution_due_at = now + timedelta(minutes=payload.resolution_minutes) if payload.resolution_minutes else None
    tracker.status = SLAStatus.active
    await session.commit(); await session.refresh(tracker)
    return tracker


async def evaluate_sla_breaches(session: AsyncSession, workspace_id: uuid.UUID) -> list[SLATracker]:
    now = datetime.now(UTC)
    result = await session.execute(select(SLATracker).where(SLATracker.workspace_id == workspace_id, SLATracker.status == SLAStatus.active, SLATracker.first_response_due_at < now, SLATracker.first_responded_at.is_(None)))
    items = list(result.scalars().all())
    for item in items:
        item.status = SLAStatus.breached; item.breached_at = now; item.escalation_level += 1
    await session.commit()
    return items


async def save_provider_credential(session: AsyncSession, workspace_id: uuid.UUID, payload: ProviderCredentialCreate) -> ProviderCredential:
    result = await session.execute(select(ProviderCredential).where(ProviderCredential.workspace_id == workspace_id, ProviderCredential.provider == payload.provider, ProviderCredential.credential_name == payload.credential_name))
    item = result.scalar_one_or_none()
    if item is None:
        item = ProviderCredential(workspace_id=workspace_id, provider=payload.provider, credential_name=payload.credential_name, encrypted_secret=encrypt_secret(payload.secret))
        session.add(item)
    else:
        item.encrypted_secret = encrypt_secret(payload.secret)
    await session.commit(); await session.refresh(item)
    return item


async def verify_identity(session: AsyncSession, workspace_id: uuid.UUID, identity_id: uuid.UUID, method: str, verified_value: str) -> IdentityVerification:
    identity = await session.get(CustomerIdentity, identity_id)
    if not identity or identity.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Identity not found")
    result = await session.execute(select(IdentityVerification).where(IdentityVerification.workspace_id == workspace_id, IdentityVerification.identity_id == identity_id))
    record = result.scalar_one_or_none()
    if record is None:
        record = IdentityVerification(workspace_id=workspace_id, identity_id=identity_id)
        session.add(record)
    record.status = IdentityVerificationStatus.verified
    record.verification_method = method
    record.verified_value_hash = hashlib.sha256(verified_value.strip().lower().encode()).hexdigest()
    record.verified_at = datetime.now(UTC)
    await session.commit(); await session.refresh(record)
    return record


async def attribution_summary(session: AsyncSession, workspace_id: uuid.UUID) -> dict:
    rows = list((await session.execute(select(AttributionTouchpoint).where(AttributionTouchpoint.workspace_id == workspace_id))).scalars().all())
    return {"total_touchpoints": len(rows), "by_channel": dict(Counter(x.channel for x in rows)), "by_source": dict(Counter(x.source for x in rows)), "by_event_type": dict(Counter(x.event_type for x in rows))}
