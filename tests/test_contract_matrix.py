import pytest

from src.mcpbridge.gateway import decide, execute
from src.mcpbridge.models import Role


READ_CASES = [
    ("github", "search_repository", {"query": "payment"}),
    ("github", "get_repository_status", {"repo": "payments-api"}),
    ("itsm", "get_incident", {"incident_id": "INC-428"}),
    ("business", "get_supplier", {"supplier_id": "SUP-ALPHA"}),
    ("business", "compare_suppliers", {"left": "SUP-ALPHA", "right": "SUP-BETA"}),
    ("business", "query_purchase_orders", {"supplier_id": "SUP-ALPHA"}),
    ("business", "generate_decision_pack", {"question": "Compare sourcing resilience"}),
]

WRITE_CASES = [
    (
        "github",
        "create_github_issue",
        {
            "repo": "payments-api",
            "title": "Synthetic CI follow-up",
            "body": "Portfolio-only write verification",
            "severity": "low",
        },
    ),
    (
        "itsm",
        "create_incident",
        {
            "title": "Synthetic incident",
            "service": "payments-api",
            "severity": "SEV-3",
            "summary": "Portfolio-only write verification",
        },
    ),
    (
        "itsm",
        "create_change_request",
        {
            "service": "payments-api",
            "summary": "Synthetic maintenance change",
            "risk": "low",
            "implementation_window": "approved test window",
        },
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("server,tool,arguments", READ_CASES)
async def test_every_allowlisted_read_executes_end_to_end(server, tool, arguments):
    outcome = await execute(
        actor="matrix-viewer",
        role=Role.VIEWER,
        server=server,
        tool=tool,
        arguments=arguments,
    )
    assert outcome["status"] == "completed"
    assert outcome["effect"] == "read"
    assert outcome["server"] == server
    assert outcome["tool"] == tool
    assert outcome["result"] is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("server,tool,arguments", WRITE_CASES)
async def test_every_allowlisted_write_requires_review_then_executes(server, tool, arguments):
    proposal = await execute(
        actor="matrix-operator",
        role=Role.OPERATOR,
        server=server,
        tool=tool,
        arguments=arguments,
    )
    assert proposal["status"] == "approval_required"
    assert proposal["effect"] == "write"
    assert "result" not in proposal

    outcome = await decide(
        actor="matrix-approver",
        role=Role.APPROVER,
        approval_token=proposal["approval_token"],
        decision="approve",
    )
    assert outcome["status"] == "completed"
    assert outcome["effect"] == "write"
    assert outcome["server"] == server
    assert outcome["tool"] == tool
    assert outcome["result"]["status"] == "created"
