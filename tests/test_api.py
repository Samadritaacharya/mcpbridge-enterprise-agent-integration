import pytest
from httpx import ASGITransport, AsyncClient

from src.mcpbridge.api import app
from src.mcpbridge.audit import reset_audit_for_tests


@pytest.fixture
async def client():
    reset_audit_for_tests()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http


@pytest.mark.asyncio
async def test_health_catalog_and_read_execution(client):
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json()["protocol_target"] == "2026-07-28"
    assert health.json()["transport"] == "streamable-http"

    catalog = await client.get("/v1/catalog")
    assert catalog.status_code == 200
    assert set(catalog.json()["servers"]) == {"github", "itsm", "business"}

    read = await client.post(
        "/v1/execute",
        headers={"x-demo-role": "viewer"},
        json={"server": "itsm", "tool": "get_incident", "arguments": {"incident_id": "INC-428"}},
    )
    assert read.status_code == 200
    assert read.json()["status"] == "completed"
    assert read.json()["result"]["id"] == "INC-428"


@pytest.mark.asyncio
async def test_agent_planning_and_auto_read(client):
    plan = await client.post("/v1/plan", json={"request": "Show incident INC-428"})
    assert plan.status_code == 200
    assert plan.json()["server"] == "itsm"
    assert plan.json()["tool"] == "get_incident"

    run = await client.post(
        "/v1/agent/run",
        headers={"x-demo-role": "viewer", "x-demo-actor": "reader-a"},
        json={"request": "Show incident INC-428"},
    )
    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert run.json()["result"]["id"] == "INC-428"


@pytest.mark.asyncio
async def test_write_requires_approval_and_approve_executes(client):
    proposed = await client.post(
        "/v1/execute",
        headers={"x-demo-role": "operator", "x-demo-actor": "operator-a"},
        json={
            "server": "itsm",
            "tool": "create_change_request",
            "arguments": {
                "service": "payments-api",
                "summary": "Rollback suspect release",
                "risk": "medium",
                "implementation_window": "approved window",
            },
        },
    )
    assert proposed.status_code == 200
    proposal = proposed.json()
    assert proposal["status"] == "approval_required"
    assert "result" not in proposal

    approved = await client.post(
        "/v1/approve",
        headers={"x-demo-role": "approver", "x-demo-actor": "approver-a"},
        json={"approval_token": proposal["approval_token"], "decision": "approve"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "completed"
    assert approved.json()["result"]["status"] == "created"


@pytest.mark.asyncio
async def test_edit_and_reject_paths(client):
    proposed = await client.post(
        "/v1/execute",
        headers={"x-demo-role": "operator"},
        json={
            "server": "github",
            "tool": "create_github_issue",
            "arguments": {
                "repo": "payments-api",
                "title": "Original",
                "body": "Original body",
                "severity": "medium",
            },
        },
    )
    token = proposed.json()["approval_token"]
    edited_arguments = {
        "repo": "payments-api",
        "title": "Reviewed title",
        "body": "Reviewed body",
        "severity": "low",
    }
    edited = await client.post(
        "/v1/approve",
        json={
            "approval_token": token,
            "decision": "edit",
            "edited_arguments": edited_arguments,
        },
    )
    assert edited.status_code == 200
    assert edited.json()["arguments"] == edited_arguments
    assert edited.json()["result"]["title"] == "Reviewed title"

    second = await client.post(
        "/v1/execute",
        headers={"x-demo-role": "operator"},
        json={
            "server": "itsm",
            "tool": "create_incident",
            "arguments": {
                "title": "Synthetic alert",
                "service": "checkout",
                "severity": "medium",
                "summary": "Synthetic only",
            },
        },
    )
    rejected = await client.post(
        "/v1/approve",
        json={"approval_token": second.json()["approval_token"], "decision": "reject"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert "result" not in rejected.json()


@pytest.mark.asyncio
async def test_fail_closed_role_schema_token_and_audit_controls(client):
    denied = await client.post(
        "/v1/execute",
        headers={"x-demo-role": "viewer"},
        json={
            "server": "itsm",
            "tool": "create_change_request",
            "arguments": {
                "service": "payments-api",
                "summary": "x",
                "risk": "medium",
                "implementation_window": "later",
            },
        },
    )
    assert denied.status_code == 403

    unknown = await client.post(
        "/v1/execute",
        json={"server": "itsm", "tool": "delete_everything", "arguments": {}},
    )
    assert unknown.status_code == 422

    extra = await client.post(
        "/v1/execute",
        json={"server": "itsm", "tool": "get_incident", "arguments": {}, "admin_override": True},
    )
    assert extra.status_code == 422

    proposed = await client.post(
        "/v1/execute",
        headers={"x-demo-role": "operator"},
        json={
            "server": "itsm",
            "tool": "create_change_request",
            "arguments": {
                "service": "payments-api",
                "summary": "x",
                "risk": "medium",
                "implementation_window": "later",
            },
        },
    )
    token = proposed.json()["approval_token"]
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    invalid = await client.post(
        "/v1/approve",
        json={"approval_token": tampered, "decision": "approve"},
    )
    assert invalid.status_code == 422

    audit = await client.get("/v1/audit")
    assert audit.status_code == 200
    assert audit.json()["events"]
    assert audit.json()["chain_valid"] is True
