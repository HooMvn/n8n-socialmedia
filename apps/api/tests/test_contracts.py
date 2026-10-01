import pytest
from pydantic import ValidationError

from app.domain import ContentStatus, PublicationStatus
from app.routes import _verify_automation_secret
from app.schemas import WorkspaceCreate
from app.settings import settings


def test_content_status_contract_is_stable() -> None:
    assert {status.value for status in ContentStatus} == {
        "draft",
        "in_review",
        "approved",
        "rejected",
        "publish_requested",
        "published",
        "failed",
    }


def test_publication_terminal_states_are_explicit() -> None:
    assert PublicationStatus.published.value == "published"
    assert PublicationStatus.failed.value == "failed"


def test_workspace_slug_rejects_unsafe_values() -> None:
    with pytest.raises(ValidationError):
        WorkspaceCreate(name="Demo", slug="Invalid Slug !")


def test_automation_secret_rejects_missing_or_wrong_value() -> None:
    with pytest.raises(Exception):
        _verify_automation_secret(None)
    with pytest.raises(Exception):
        _verify_automation_secret("wrong-secret")


def test_automation_secret_accepts_configured_value() -> None:
    _verify_automation_secret(settings.n8n_webhook_secret)
