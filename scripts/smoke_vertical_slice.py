"""Run the first Risheh Engage vertical slice against a running local API.

Usage:
    python scripts/smoke_vertical_slice.py

Requires:
    pip install httpx
    docker compose up --build
"""

from __future__ import annotations

import os
import time

import httpx

API = os.getenv("API_BASE_URL", "http://localhost:8000")


def request(client: httpx.Client, method: str, path: str, **kwargs):
    response = client.request(method, f"{API}{path}", timeout=15, **kwargs)
    response.raise_for_status()
    return response.json()


def main() -> None:
    suffix = str(int(time.time()))
    with httpx.Client() as client:
        workspace = request(
            client,
            "POST",
            "/api/v1/workspaces",
            json={"name": "Smoke Test Workspace", "slug": f"smoke-{suffix}"},
        )
        workspace_id = workspace["id"]
        print("✓ workspace", workspace_id)

        brand = request(
            client,
            "PUT",
            f"/api/v1/workspaces/{workspace_id}/brand",
            json={
                "name": "Smoke Brand",
                "tone_of_voice": "clear, human, professional",
                "audience": "test audience",
                "forbidden_terms": "fabricated claims",
            },
        )
        print("✓ brand", brand["id"])

        content = request(
            client,
            "POST",
            f"/api/v1/workspaces/{workspace_id}/contents",
            json={
                "brand_id": brand["id"],
                "title": "Smoke content",
                "body": "This content validates the application lifecycle; it is not published externally.",
                "platform": "telegram",
            },
        )
        content_id = content["id"]
        print("✓ draft", content_id)

        review = request(
            client,
            "POST",
            f"/api/v1/workspaces/{workspace_id}/contents/{content_id}/submit-review",
        )
        assert review["status"] == "in_review"
        print("✓ review")

        approved = request(
            client,
            "POST",
            f"/api/v1/workspaces/{workspace_id}/contents/{content_id}/approve",
            json={"actor": "smoke-test", "note": "automated lifecycle validation"},
        )
        assert approved["status"] == "approved"
        print("✓ approval")

        publication = request(
            client,
            "POST",
            f"/api/v1/workspaces/{workspace_id}/contents/{content_id}/publish",
            json={"idempotency_key": f"smoke:{content_id}"},
        )
        assert publication["status"] == "pending"
        print("✓ publication", publication["id"])

        # Replaying the exact publish command must return the same Publication.
        replay = request(
            client,
            "POST",
            f"/api/v1/workspaces/{workspace_id}/contents/{content_id}/publish",
            json={"idempotency_key": f"smoke:{content_id}"},
        )
        assert replay["id"] == publication["id"]
        print("✓ idempotent replay")

    print("\nVertical Slice 01 smoke test passed through the Outbox boundary.")
    print("No external social post was created by this test.")


if __name__ == "__main__":
    main()
