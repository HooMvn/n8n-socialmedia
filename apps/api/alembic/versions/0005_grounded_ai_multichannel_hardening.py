"""Grounded AI, consent, SLA, provider credentials, identity verification.

Revision ID: 0005_grounded_ai
Revises: 0004_ai_outbound_attribution
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_grounded_ai"
down_revision: str | None = "0004_ai_outbound_attribution"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

knowledge_source_status = postgresql.ENUM("active", "disabled", name="knowledge_source_status", create_type=False)
consent_status = postgresql.ENUM("granted", "revoked", "unknown", name="consent_status", create_type=False)
sla_status = postgresql.ENUM("active", "breached", "resolved", name="sla_status", create_type=False)
provider_credential_status = postgresql.ENUM("active", "disabled", "invalid", name="provider_credential_status", create_type=False)
identity_verification_status = postgresql.ENUM("unverified", "verified", "conflicted", name="identity_verification_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in [knowledge_source_status, consent_status, sla_status, provider_credential_status, identity_verification_status]:
        enum_type.create(bind, checkfirst=True)
    op.create_table("knowledge_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(180), nullable=False), sa.Column("source_type", sa.String(40), nullable=False), sa.Column("source_uri", sa.String(1000), nullable=False, server_default=""), sa.Column("status", knowledge_source_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_knowledge_sources_workspace_id", "knowledge_sources", ["workspace_id"])
    op.create_table("knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False), sa.Column("chunk_index", sa.Integer(), nullable=False), sa.Column("title", sa.String(255), nullable=False, server_default=""), sa.Column("body", sa.Text(), nullable=False), sa.Column("checksum", sa.String(128), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("source_id", "chunk_index", name="uq_knowledge_chunk_index"))
    op.create_table("retrieval_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("ai_draft_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_reply_drafts.id", ondelete="CASCADE"), nullable=False), sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), nullable=False), sa.Column("rank", sa.Integer(), nullable=False), sa.Column("score", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False), sa.Column("purpose", sa.String(80), nullable=False), sa.Column("channel", sa.String(40), nullable=False), sa.Column("status", consent_status, nullable=False), sa.Column("evidence", sa.Text(), nullable=False, server_default=""), sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("workspace_id", "customer_id", "purpose", "channel", name="uq_customer_consent_scope"))
    op.create_table("sla_trackers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False), sa.Column("status", sla_status, nullable=False), sa.Column("first_response_due_at", sa.DateTime(timezone=True), nullable=False), sa.Column("resolution_due_at", sa.DateTime(timezone=True)), sa.Column("first_responded_at", sa.DateTime(timezone=True)), sa.Column("breached_at", sa.DateTime(timezone=True)), sa.Column("escalation_level", sa.Integer(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("workspace_id", "conversation_id", name="uq_sla_conversation"))
    op.create_table("provider_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("provider", sa.String(40), nullable=False), sa.Column("credential_name", sa.String(100), nullable=False), sa.Column("encrypted_secret", sa.Text(), nullable=False), sa.Column("status", provider_credential_status, nullable=False), sa.Column("last_verified_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("workspace_id", "provider", "credential_name", name="uq_provider_credential_workspace"))
    op.create_table("identity_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("identity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_identities.id", ondelete="CASCADE"), nullable=False), sa.Column("status", identity_verification_status, nullable=False), sa.Column("verification_method", sa.String(80), nullable=False, server_default=""), sa.Column("verified_value_hash", sa.String(128), nullable=False, server_default=""), sa.Column("verified_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("workspace_id", "identity_id", name="uq_identity_verification"))


def downgrade() -> None:
    for table in ["identity_verifications", "provider_credentials", "sla_trackers", "consent_records", "retrieval_evidence", "knowledge_chunks", "knowledge_sources"]:
        op.drop_table(table)
    bind = op.get_bind()
    for enum_type in [identity_verification_status, provider_credential_status, sla_status, consent_status, knowledge_source_status]:
        enum_type.drop(bind, checkfirst=True)
