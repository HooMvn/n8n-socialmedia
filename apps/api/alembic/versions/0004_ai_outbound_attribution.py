"""Add AI drafts, outbound messages and attribution touchpoints.

Revision ID: 0004_ai_outbound_attribution
Revises: 0003_customer_communication
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_ai_outbound_attribution"
down_revision: str | None = "0003_customer_communication"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ai_draft_status = postgresql.ENUM("pending", "approved", "rejected", name="ai_draft_status", create_type=False)
outbound_status = postgresql.ENUM("queued", "sent", "delivered", "failed", "cancelled", name="outbound_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    ai_draft_status.create(bind, checkfirst=True)
    outbound_status.create(bind, checkfirst=True)

    op.create_table(
        "ai_reply_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intent", sa.String(80), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", ai_draft_status, nullable=False),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_reply_drafts_workspace_id", "ai_reply_drafts", ["workspace_id"])
    op.create_index("ix_ai_reply_drafts_conversation_id", "ai_reply_drafts", ["conversation_id"])
    op.create_index("ix_ai_reply_drafts_status", "ai_reply_drafts", ["status"])

    op.create_table(
        "outbound_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_draft_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_reply_drafts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(180), nullable=False),
        sa.Column("status", outbound_status, nullable=False),
        sa.Column("external_message_id", sa.String(255), nullable=True),
        sa.Column("error_code", sa.String(120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "idempotency_key", name="uq_outbound_idempotency"),
    )
    op.create_index("ix_outbound_messages_workspace_id", "outbound_messages", ["workspace_id"])
    op.create_index("ix_outbound_messages_conversation_id", "outbound_messages", ["conversation_id"])
    op.create_index("ix_outbound_messages_customer_id", "outbound_messages", ["customer_id"])
    op.create_index("ix_outbound_messages_status", "outbound_messages", ["status"])

    op.create_table(
        "attribution_touchpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("campaign", sa.String(180), nullable=False, server_default=""),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_attribution_touchpoints_workspace_id", "attribution_touchpoints", ["workspace_id"])
    op.create_index("ix_attribution_touchpoints_customer_id", "attribution_touchpoints", ["customer_id"])


def downgrade() -> None:
    op.drop_table("attribution_touchpoints")
    op.drop_table("outbound_messages")
    op.drop_table("ai_reply_drafts")
    bind = op.get_bind()
    outbound_status.drop(bind, checkfirst=True)
    ai_draft_status.drop(bind, checkfirst=True)
