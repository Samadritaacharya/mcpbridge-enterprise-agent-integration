from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from .models import Effect, Role, ToolPolicy


POLICIES: dict[tuple[str, str], ToolPolicy] = {}


def _register(policy: ToolPolicy) -> None:
    POLICIES[(policy.server, policy.name)] = policy


for policy in [
    ToolPolicy("github", "search_repository", Effect.READ, (Role.VIEWER, Role.OPERATOR, Role.APPROVER), False, "Search synthetic repository metadata."),
    ToolPolicy("github", "get_repository_status", Effect.READ, (Role.VIEWER, Role.OPERATOR, Role.APPROVER), False, "Read CI/deployment status."),
    ToolPolicy("github", "create_github_issue", Effect.WRITE, (Role.OPERATOR, Role.APPROVER), True, "Create a synthetic GitHub issue."),
    ToolPolicy("itsm", "get_incident", Effect.READ, (Role.VIEWER, Role.OPERATOR, Role.APPROVER), False, "Read incident details."),
    ToolPolicy("itsm", "create_incident", Effect.WRITE, (Role.OPERATOR, Role.APPROVER), True, "Create a synthetic incident."),
    ToolPolicy("itsm", "create_change_request", Effect.WRITE, (Role.OPERATOR, Role.APPROVER), True, "Create a synthetic change request."),
    ToolPolicy("business", "get_supplier", Effect.READ, (Role.VIEWER, Role.OPERATOR, Role.APPROVER), False, "Read supplier data."),
    ToolPolicy("business", "compare_suppliers", Effect.READ, (Role.VIEWER, Role.OPERATOR, Role.APPROVER), False, "Compare two suppliers."),
    ToolPolicy("business", "query_purchase_orders", Effect.READ, (Role.VIEWER, Role.OPERATOR, Role.APPROVER), False, "Read purchase orders."),
    ToolPolicy("business", "generate_decision_pack", Effect.READ, (Role.VIEWER, Role.OPERATOR, Role.APPROVER), False, "Create an evidence-backed decision summary."),
]:
    _register(policy)


def get_policy(server: str, tool: str) -> ToolPolicy:
    try:
        return POLICIES[(server, tool)]
    except KeyError as exc:
        raise ValueError(f"tool is not allowlisted: {server}.{tool}") from exc


def authorize(role: Role, server: str, tool: str) -> ToolPolicy:
    policy = get_policy(server, tool)
    if role not in policy.allowed_roles:
        raise PermissionError(f"role {role.value} cannot call {server}.{tool}")
    return policy


def _secret() -> bytes:
    value = os.getenv("MCPBRIDGE_APPROVAL_SECRET", "mcpbridge-local-dev-secret")
    if os.getenv("MCPBRIDGE_ENV") == "production" and value == "mcpbridge-local-dev-secret":
        raise RuntimeError("MCPBRIDGE_APPROVAL_SECRET must be configured in production")
    return value.encode()


def mint_approval_token(*, actor: str, role: Role, server: str, tool: str, arguments: dict[str, Any], ttl_seconds: int = 300) -> str:
    policy = authorize(role, server, tool)
    if not policy.approval_required:
        raise ValueError("approval token requested for a read-only tool")
    now = int(time.time())
    body = {
        "v": 1,
        "actor": actor,
        "role": role.value,
        "server": server,
        "tool": tool,
        "arguments": arguments,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(_secret(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=") + "." + base64.urlsafe_b64encode(sig).decode().rstrip("=")


def verify_approval_token(token: str) -> dict[str, Any]:
    try:
        left, right = token.split(".", 1)

        def pad(value: str) -> str:
            return value + "=" * (-len(value) % 4)

        raw = base64.urlsafe_b64decode(pad(left))
        supplied = base64.urlsafe_b64decode(pad(right))
        expected = hmac.new(_secret(), raw, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied, expected):
            raise ValueError("invalid approval token signature")
        body = json.loads(raw)
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("malformed approval token") from exc
    if int(body.get("exp", 0)) < int(time.time()):
        raise ValueError("approval token expired")
    policy = get_policy(str(body["server"]), str(body["tool"]))
    if not policy.approval_required:
        raise ValueError("token references a non-sensitive tool")
    return body
