import pytest

from src.mcpbridge.audit import reset_audit_for_tests
from src.mcpbridge.gateway import decide, execute
from src.mcpbridge.models import Role


@pytest.mark.asyncio
async def test_read_executes_automatically_through_mcp():
    reset_audit_for_tests()
    result = await execute(
        actor="reader",
        role=Role.VIEWER,
        server="itsm",
        tool="get_incident",
        arguments={"incident_id": "INC-428"},
    )
    assert result["status"] == "completed"
    assert result["effect"] == "read"
    assert result["result"]["id"] == "INC-428"


@pytest.mark.asyncio
async def test_write_requires_approval_then_executes():
    reset_audit_for_tests()
    proposed = await execute(
        actor="operator-a",
        role=Role.OPERATOR,
        server="itsm",
        tool="create_change_request",
        arguments={
            "service": "payments-api",
            "summary": "Rollback suspect release",
            "risk": "medium",
            "implementation_window": "approved window",
        },
    )
    assert proposed["status"] == "approval_required"
    assert "result" not in proposed

    completed = await decide(
        actor="approver-a",
        role=Role.APPROVER,
        approval_token=proposed["approval_token"],
        decision="approve",
    )
    assert completed["status"] == "completed"
    assert completed["result"]["status"] == "created"


@pytest.mark.asyncio
async def test_edit_replaces_arguments_before_mcp_execution():
    proposed = await execute(
        actor="operator-a",
        role=Role.OPERATOR,
        server="github",
        tool="create_github_issue",
        arguments={
            "repo": "payments-api",
            "title": "Original",
            "body": "Original body",
            "severity": "medium",
        },
    )
    edited = {
        "repo": "payments-api",
        "title": "Approved title",
        "body": "Reviewed body",
        "severity": "low",
    }
    completed = await decide(
        actor="approver-a",
        role=Role.APPROVER,
        approval_token=proposed["approval_token"],
        decision="edit",
        edited_arguments=edited,
    )
    assert completed["arguments"] == edited
    assert completed["result"]["title"] == "Approved title"


@pytest.mark.asyncio
async def test_viewer_cannot_propose_write():
    with pytest.raises(PermissionError):
        await execute(
            actor="viewer-a",
            role=Role.VIEWER,
            server="itsm",
            tool="create_incident",
            arguments={
                "title": "x",
                "service": "payments-api",
                "severity": "SEV-2",
                "summary": "x",
            },
        )
