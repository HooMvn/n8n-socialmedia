"""Add customer communication domain tables.

Revision ID: 0003_customer_communication
Revises: 0002_auth_outbox
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_customer_communication"
down_revision: str | None = "0002_auth_outbox"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

conversation_status = postgresql.ENUM(
    "open",
    "waiting_human",
    "resolved",
    "closed",
    name="conversation_status",
    create_type=False,
)
message_direction = postgresql.ENUM(
    "inbound",
    "outbound",
    name="message_direction",
    create_type=False,
)
message_author_type = postgresql.ENUM(
    "customer",
    "ai",
    "human",
    "system",
    name="message_author_type",
    create_type=False,
)
lead_status = postgresql.ENUM(
    "new",
    "qualified",
    "contacted",
    "proposal",
    "won",
    "lost",
    name="lead_status",
    create_type=False,
)
follow_up_status = postgresql.ENUM(
    "pending",
    "done",
    "cancelled",
    name="follow_up_status",
    create_type=False,
)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in [
        conversation_status,
        message_direction,
        message_author_type,
        lead_status,
        follow_up_status,
    ]:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        *_timestamps(),
    )
    op.create_index("ix_customers_workspace_id", "customers", ["workspace_id"])
    op.create_index("ix_customers_phone", "customers", ["phone"])
    op.create_index("ix_customers_email", "customers", ["email"])

    op.create_table(
        "customer_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("external_user_id", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint(
            "workspace_id",
            "channel",
            "external_user_id",
            name="uq_customer_identity_channel",
        ),
    )
    op.create_index(
        "ix_customer_identities_workspace_id",
        "customer_identities",
        ["workspace_id"],
    )
    op.create_index(
        "ix_customer_identities_customer_id",
        "customer_identities",
        ["customer_id"],
    )
    op.create_index(
        "ix_customer_identities_channel",
        "customer_identities",
        ["channel"],
    )

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("status", conversation_status, nullable=False),
        sa.Column(
            "assigned_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "last_message_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("intent", sa.String(80), nullable=True),
        sa.Column("intent_confidence", sa.Integer(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_conversations_workspace_id", "conversations", ["workspace_id"])
    op.create_index("ix_conversations_customer_id", "conversations", ["customer_id"])
    op.create_index("ix_conversations_last_message_at", "conversations", ["last_message_at"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("external_message_id", sa.String(255), nullable=False),
        sa.Column("direction", message_direction, nullable=False),
        sa.Column("author_type", message_author_type, nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint(
            "workspace_id",
            "channel",
            "external_message_id",
            name="uq_message_external_id",
        ),
    )
    op.create_index("ix_messages_workspace_id", "messages", ["workspace_id"])
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_channel", sa.String(40), nullable=False),
        sa.Column("status", lead_status, nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("interest", sa.String(255), nullable=False, server_default=""),
        *_timestamps(),
        sa.UniqueConstraint(
            "workspace_id",
            "customer_id",
            name="uq_lead_customer_workspace",
        ),
    )
    op.create_index("ix_leads_workspace_id", "leads", ["workspace_id"])
    op.create_index("ix_leads_status", "leads", ["status"])

    op.create_table(
        "follow_ups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lead_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", follow_up_status, nullable=False),
        sa.Column("reason", sa.String(255), nullable=False, server_default=""),
        sa.Column(
            "assigned_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_timestamps(),
    )
    op.create_index("ix_follow_ups_workspace_id", "follow_ups", ["workspace_id"])
    op.create_index("ix_follow_ups_due_at", "follow_ups", ["due_at"])


def downgrade() -> None:
    for table in [
        "follow_ups",
        "leads",
        "messages",
        "conversations",
        "customer_identities",
        "customers",
    ]:
        op.drop_table(table)

    bind = op.get_bind()
    for enum_type in [
        follow_up_status,
        lead_status,
        message_author_type,
        message_direction,
        conversation_status,
    ]:
        enum_type.drop(bind, checkfirst=True)
