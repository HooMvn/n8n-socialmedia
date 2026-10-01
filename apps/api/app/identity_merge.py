from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_domain import Conversation, Customer, CustomerIdentity, FollowUp, Lead, Message
from app.engagement_domain import AttributionTouchpoint, OutboundMessage
from app.hardening_domain import ConsentRecord, IdentityVerification, IdentityVerificationStatus


async def merge_verified_identities(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    source_customer_id: uuid.UUID,
    target_customer_id: uuid.UUID,
    identity_ids: list[uuid.UUID],
) -> Customer:
    if source_customer_id == target_customer_id:
        raise HTTPException(status_code=409, detail="Source and target customer are identical")

    source = await session.get(Customer, source_customer_id)
    target = await session.get(Customer, target_customer_id)
    if not source or not target or source.workspace_id != workspace_id or target.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Customer not found in workspace")

    identities = list((await session.execute(select(CustomerIdentity).where(
        CustomerIdentity.workspace_id == workspace_id,
        CustomerIdentity.customer_id == source_customer_id,
        CustomerIdentity.id.in_(identity_ids),
    ))).scalars().all())
    if len(identities) != len(set(identity_ids)):
        raise HTTPException(status_code=409, detail="Selected identity does not belong to source customer")

    verified = list((await session.execute(select(IdentityVerification).where(
        IdentityVerification.workspace_id == workspace_id,
        IdentityVerification.identity_id.in_(identity_ids),
        IdentityVerification.status == IdentityVerificationStatus.verified,
    ))).scalars().all())
    if len(verified) != len(set(identity_ids)):
        raise HTTPException(status_code=409, detail="All identities must be verified before merge")

    for identity in identities:
        conflict = (await session.execute(select(CustomerIdentity).where(
            CustomerIdentity.workspace_id == workspace_id,
            CustomerIdentity.customer_id == target_customer_id,
            CustomerIdentity.channel == identity.channel,
            CustomerIdentity.external_user_id == identity.external_user_id,
        ))).scalar_one_or_none()
        if conflict:
            raise HTTPException(status_code=409, detail="Target has conflicting provider identity")

    source_lead = (await session.execute(select(Lead).where(
        Lead.workspace_id == workspace_id,
        Lead.customer_id == source_customer_id,
    ))).scalar_one_or_none()
    target_lead = (await session.execute(select(Lead).where(
        Lead.workspace_id == workspace_id,
        Lead.customer_id == target_customer_id,
    ))).scalar_one_or_none()

    if source_lead and target_lead:
        await session.execute(update(FollowUp).where(
            FollowUp.workspace_id == workspace_id,
            FollowUp.lead_id == source_lead.id,
        ).values(lead_id=target_lead.id))
        target_lead.score = max(target_lead.score, source_lead.score)
        if not target_lead.interest and source_lead.interest:
            target_lead.interest = source_lead.interest
        await session.delete(source_lead)
    elif source_lead:
        source_lead.customer_id = target_customer_id

    source_consents = list((await session.execute(select(ConsentRecord).where(
        ConsentRecord.workspace_id == workspace_id,
        ConsentRecord.customer_id == source_customer_id,
    ))).scalars().all())
    for consent in source_consents:
        existing = (await session.execute(select(ConsentRecord).where(
            ConsentRecord.workspace_id == workspace_id,
            ConsentRecord.customer_id == target_customer_id,
            ConsentRecord.purpose == consent.purpose,
            ConsentRecord.channel == consent.channel,
        ))).scalar_one_or_none()
        if existing:
            if existing.status.value == "unknown" and consent.status.value != "unknown":
                existing.status = consent.status
                existing.evidence = consent.evidence
                existing.effective_at = consent.effective_at
            await session.delete(consent)
        else:
            consent.customer_id = target_customer_id

    await session.execute(update(CustomerIdentity).where(CustomerIdentity.id.in_(identity_ids)).values(customer_id=target_customer_id))
    await session.execute(update(Conversation).where(Conversation.workspace_id == workspace_id, Conversation.customer_id == source_customer_id).values(customer_id=target_customer_id))
    await session.execute(update(Message).where(Message.workspace_id == workspace_id, Message.customer_id == source_customer_id).values(customer_id=target_customer_id))
    await session.execute(update(OutboundMessage).where(OutboundMessage.workspace_id == workspace_id, OutboundMessage.customer_id == source_customer_id).values(customer_id=target_customer_id))
    await session.execute(update(AttributionTouchpoint).where(AttributionTouchpoint.workspace_id == workspace_id, AttributionTouchpoint.customer_id == source_customer_id).values(customer_id=target_customer_id))

    if not target.phone and source.phone:
        target.phone = source.phone
    if not target.email and source.email:
        target.email = source.email
    target.notes = (target.notes + "\n" + f"Verified merge from customer {source.id}").strip()

    remaining = (await session.execute(select(CustomerIdentity).where(
        CustomerIdentity.workspace_id == workspace_id,
        CustomerIdentity.customer_id == source_customer_id,
    ))).scalars().first()
    if remaining is None:
        await session.delete(source)

    await session.commit()
    await session.refresh(target)
    return target
