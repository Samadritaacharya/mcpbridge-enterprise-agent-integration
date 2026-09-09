import pytest

from src.mcpbridge.models import Role
from src.mcpbridge.policy import authorize, mint_approval_token, verify_approval_token


def test_read_policy_allows_viewer():
    policy = authorize(Role.VIEWER, "itsm", "get_incident")
    assert policy.approval_required is False


def test_write_policy_blocks_viewer():
    with pytest.raises(PermissionError):
        authorize(Role.VIEWER, "itsm", "create_change_request")


def test_unknown_tool_fails_closed():
    with pytest.raises(ValueError, match="not allowlisted"):
        authorize(Role.APPROVER, "itsm", "delete_everything")


def test_signed_approval_token_round_trip(monkeypatch):
    monkeypatch.setenv("MCPBRIDGE_APPROVAL_SECRET", "test-secret")
    token = mint_approval_token(
        actor="sam",
        role=Role.OPERATOR,
        server="github",
        tool="create_github_issue",
        arguments={"repo": "payments-api", "title": "x", "body": "y"},
    )
    body = verify_approval_token(token)
    assert body["server"] == "github"
    assert body["tool"] == "create_github_issue"
    assert body["arguments"]["repo"] == "payments-api"


def test_tampered_approval_token_is_rejected(monkeypatch):
    monkeypatch.setenv("MCPBRIDGE_APPROVAL_SECRET", "test-secret")
    token = mint_approval_token(
        actor="sam",
        role=Role.OPERATOR,
        server="itsm",
        tool="create_change_request",
        arguments={"service": "payments-api"},
    )
    left, right = token.split(".")
    tampered = left[:-1] + ("A" if left[-1] != "A" else "B") + "." + right
    with pytest.raises(ValueError):
        verify_approval_token(tampered)
