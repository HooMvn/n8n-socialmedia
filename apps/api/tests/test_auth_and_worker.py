import uuid

from app.auth import create_access_token, hash_password, verify_password
from app.domain import Membership, User, WorkspaceRole
from app.outbox_worker import backoff_seconds


def test_password_hash_round_trip() -> None:
    encoded = hash_password("Correct-Horse-12345")
    assert encoded != "Correct-Horse-12345"
    assert verify_password("Correct-Horse-12345", encoded)
    assert not verify_password("wrong-password", encoded)


def test_access_token_is_created() -> None:
    user = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        password_hash="not-used-here",
        full_name="Owner",
        is_active=True,
    )
    token = create_access_token(user)
    assert isinstance(token, str)
    assert token.count(".") == 2


def test_workspace_roles_are_explicit() -> None:
    membership = Membership(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role=WorkspaceRole.reviewer,
    )
    assert membership.role == WorkspaceRole.reviewer
    assert membership.role != WorkspaceRole.editor


def test_outbox_backoff_is_bounded() -> None:
    assert backoff_seconds(1) == 2
    assert backoff_seconds(2) == 4
    assert backoff_seconds(20) == 300
