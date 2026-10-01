from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.domain import Workspace


DATABASE_URL = os.getenv("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL is required for PostgreSQL integration tests",
)


@pytest.mark.asyncio
async def test_alembic_schema_is_present() -> None:
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as connection:
        revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
        tables = set(
            (
                await connection.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema='public'"
                    )
                )
            ).scalars()
        )
    await engine.dispose()

    assert revision
    assert {
        "workspaces",
        "customers",
        "conversations",
        "outbox_events",
        "knowledge_sources",
        "provider_credentials",
    }.issubset(tables)


@pytest.mark.asyncio
async def test_workspace_slug_unique_constraint_is_enforced() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    slug = f"integration-{uuid.uuid4().hex[:12]}"

    async with session_factory() as session:
        first = Workspace(name="Integration A", slug=slug)
        session.add(first)
        await session.commit()
        first_id = first.id

    try:
        async with session_factory() as session:
            session.add(Workspace(name="Integration B", slug=slug))
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()
    finally:
        async with session_factory() as session:
            await session.execute(text("DELETE FROM workspaces WHERE id = :id"), {"id": first_id})
            await session.commit()
        await engine.dispose()
