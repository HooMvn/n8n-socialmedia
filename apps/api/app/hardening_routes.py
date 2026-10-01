from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_roles, require_workspace_member
from app.communication_domain import Customer
from app.database import get_session
from app.domain import Membership, WorkspaceRole
from app.engagement_schemas import AIDraftRead
from app.hardening_domain import KnowledgeChunk, KnowledgeSource, ProviderCredential, RetrievalEvidence
from app.hardening_schemas import (
    AttributionSummary,
    ConsentRead,
    ConsentUpsert,
    GroundedDraftRequest,
    IdentityMergeRequest,
    IdentityVerificationRead,
    IdentityVerifyRequest,
    KnowledgeSourceCreate,
    KnowledgeSourceRead,
    ProviderCredentialCreate,
    ProviderCredentialRead,
    SLARead,
    SLAStart,
)
from app.hardening_services import (
    attribution_summary,
    create_knowledge_source,
    evaluate_sla_breaches,
    grounded_draft,
    save_provider_credential,
    start_sla,
    upsert_consent,
    verify_identity,
)
from app.identity_merge import merge_verified_identities

router = APIRouter(prefix="/api/v1", tags=["hardening-v0.7"])


@router.post("/workspaces/{workspace_id}/knowledge/sources", response_model=KnowledgeSourceRead, status_code=201)
async def add_knowledge_source(workspace_id: uuid.UUID, payload: KnowledgeSourceCreate, _: Membership = Depends(require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.editor)), session: AsyncSession = Depends(get_session)):
    return await create_knowledge_source(session, workspace_id, payload)


@router.get("/workspaces/{workspace_id}/knowledge/sources", response_model=list[KnowledgeSourceRead])
async def list_knowledge_sources(workspace_id: uuid.UUID, _: Membership = Depends(require_workspace_member), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(KnowledgeSource).where(KnowledgeSource.workspace_id == workspace_id).order_by(KnowledgeSource.created_at.desc()))
    return list(result.scalars().all())


@router.post("/workspaces/{workspace_id}/conversations/{conversation_id}/ai/grounded-drafts", response_model=AIDraftRead, status_code=201)
async def create_grounded_draft(workspace_id: uuid.UUID, conversation_id: uuid.UUID, payload: GroundedDraftRequest, _: Membership = Depends(require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.editor, WorkspaceRole.reviewer)), session: AsyncSession = Depends(get_session)):
    return await grounded_draft(session, workspace_id, conversation_id, payload.source_message_id, payload.max_chunks)


@router.get("/workspaces/{workspace_id}/ai/drafts/{draft_id}/evidence")
async def draft_evidence(workspace_id: uuid.UUID, draft_id: uuid.UUID, _: Membership = Depends(require_workspace_member), session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(RetrievalEvidence, KnowledgeChunk)
        .join(KnowledgeChunk, KnowledgeChunk.id == RetrievalEvidence.chunk_id)
        .where(RetrievalEvidence.workspace_id == workspace_id, RetrievalEvidence.ai_draft_id == draft_id)
        .order_by(RetrievalEvidence.rank.asc())
    )
    return [
        {"chunk_id": str(evidence.chunk_id), "source_id": str(chunk.source_id), "title": chunk.title, "body": chunk.body, "rank": evidence.rank, "score": evidence.score}
        for evidence, chunk in result.all()
    ]


@router.put("/workspaces/{workspace_id}/customers/{customer_id}/consent", response_model=ConsentRead)
async def set_consent(workspace_id: uuid.UUID, customer_id: uuid.UUID, payload: ConsentUpsert, _: Membership = Depends(require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)), session: AsyncSession = Depends(get_session)):
    return await upsert_consent(session, workspace_id, customer_id, payload)


@router.post("/workspaces/{workspace_id}/conversations/{conversation_id}/sla", response_model=SLARead)
async def begin_sla(workspace_id: uuid.UUID, conversation_id: uuid.UUID, payload: SLAStart, _: Membership = Depends(require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)), session: AsyncSession = Depends(get_session)):
    return await start_sla(session, workspace_id, conversation_id, payload)


@router.post("/workspaces/{workspace_id}/sla/evaluate", response_model=list[SLARead])
async def evaluate_sla(workspace_id: uuid.UUID, _: Membership = Depends(require_roles(WorkspaceRole.owner, WorkspaceRole.admin)), session: AsyncSession = Depends(get_session)):
    return await evaluate_sla_breaches(session, workspace_id)


@router.post("/workspaces/{workspace_id}/identities/{identity_id}/verify", response_model=IdentityVerificationRead)
async def verify_customer_identity(workspace_id: uuid.UUID, identity_id: uuid.UUID, payload: IdentityVerifyRequest, _: Membership = Depends(require_roles(WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.reviewer)), session: AsyncSession = Depends(get_session)):
    return await verify_identity(session, workspace_id, identity_id, payload.verification_method, payload.verified_value)


@router.post("/workspaces/{workspace_id}/customers/merge")
async def merge_customers(workspace_id: uuid.UUID, payload: IdentityMergeRequest, _: Membership = Depends(require_roles(WorkspaceRole.owner, WorkspaceRole.admin)), session: AsyncSession = Depends(get_session)):
    customer: Customer = await merge_verified_identities(session, workspace_id, payload.source_customer_id, payload.target_customer_id, payload.verified_identity_ids)
    return {"customer_id": str(customer.id), "display_name": customer.display_name, "merged": True}


@router.put("/workspaces/{workspace_id}/providers/credentials", response_model=ProviderCredentialRead)
async def upsert_provider_credential(workspace_id: uuid.UUID, payload: ProviderCredentialCreate, _: Membership = Depends(require_roles(WorkspaceRole.owner, WorkspaceRole.admin)), session: AsyncSession = Depends(get_session)):
    item = await save_provider_credential(session, workspace_id, payload)
    return ProviderCredentialRead(id=item.id, provider=item.provider, credential_name=item.credential_name, status=item.status.value, last_verified_at=item.last_verified_at)


@router.get("/workspaces/{workspace_id}/providers/credentials", response_model=list[ProviderCredentialRead])
async def list_provider_credentials(workspace_id: uuid.UUID, _: Membership = Depends(require_roles(WorkspaceRole.owner, WorkspaceRole.admin)), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ProviderCredential).where(ProviderCredential.workspace_id == workspace_id).order_by(ProviderCredential.provider.asc()))
    return [ProviderCredentialRead(id=x.id, provider=x.provider, credential_name=x.credential_name, status=x.status.value, last_verified_at=x.last_verified_at) for x in result.scalars().all()]


@router.get("/workspaces/{workspace_id}/analytics/attribution", response_model=AttributionSummary)
async def get_attribution_summary(workspace_id: uuid.UUID, _: Membership = Depends(require_workspace_member), session: AsyncSession = Depends(get_session)):
    return await attribution_summary(session, workspace_id)
