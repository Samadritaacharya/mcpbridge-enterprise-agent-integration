from __future__ import annotations

from typing import Any

from mcp import Client

from .audit import append_audit
from .models import Role
from .policy import authorize, mint_approval_token, verify_approval_token
from .servers import build_servers


def _application_data(structured: Any) -> Any:
    """Normalize SDK wrappers while preserving real structured tool objects.

    MCP v2 wraps primitive/list structured outputs as ``{"result": ...}`` because the
    generated output schema must be an object. Dict-shaped tool results are already returned
    as their application object. MCPBridge unwraps only the single-key SDK wrapper so the
    gateway contract stays natural for both shapes.
    """

    if isinstance(structured, dict) and set(structured) == {"result"}:
        return structured["result"]
    return structured


async def call_mcp_tool(server: str, tool: str, arguments: dict[str, Any]) -> Any:
    """Execute a call through the official MCP Client protocol layer."""

    servers = build_servers()
    if server not in servers:
        raise ValueError(f"unknown MCP server: {server}")
    async with Client(servers[server], raise_exceptions=True) as client:
        result = await client.call_tool(tool, arguments)
        if result.is_error:
            raise RuntimeError(f"MCP tool returned an error: {server}.{tool}")
        if result.structured_content is None:
            raise RuntimeError(
                f"MCP tool did not return structured application data: {server}.{tool}"
            )
        return _application_data(result.structured_content)


async def execute(
    *,
    actor: str,
    role: Role,
    server: str,
    tool: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Apply the allowlist/RBAC boundary before any MCP invocation."""

    policy = authorize(role, server, tool)
    if policy.approval_required:
        token = mint_approval_token(
            actor=actor,
            role=role,
            server=server,
            tool=tool,
            arguments=arguments,
        )
        event = append_audit(
            actor=actor,
            role=role.value,
            phase="proposed",
            server=server,
            tool=tool,
            decision="approval_required",
            arguments=arguments,
        )
        return {
            "status": "approval_required",
            "effect": policy.effect.value,
            "server": server,
            "tool": tool,
            "arguments": arguments,
            "approval_token": token,
            "audit_event": event.__dict__,
            "message": (
                "Sensitive MCP write tool is blocked until an approver explicitly "
                "approves, edits or rejects the proposed call."
            ),
        }

    result = await call_mcp_tool(server, tool, arguments)
    event = append_audit(
        actor=actor,
        role=role.value,
        phase="executed",
        server=server,
        tool=tool,
        decision="auto-read",
        arguments=arguments,
    )
    return {
        "status": "completed",
        "effect": policy.effect.value,
        "server": server,
        "tool": tool,
        "arguments": arguments,
        "result": result,
        "audit_event": event.__dict__,
    }


async def decide(
    *,
    actor: str,
    role: Role,
    approval_token: str,
    decision: str,
    edited_arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if role is not Role.APPROVER:
        raise PermissionError("only the approver role can approve MCP write execution")

    body = verify_approval_token(approval_token)
    if decision not in {"approve", "edit", "reject"}:
        raise ValueError("decision must be approve, edit or reject")

    if decision == "edit":
        if not edited_arguments:
            raise ValueError("edited_arguments are required when decision=edit")
        arguments = edited_arguments
    else:
        arguments = body["arguments"]

    if decision == "reject":
        event = append_audit(
            actor=actor,
            role=role.value,
            phase="reviewed",
            server=body["server"],
            tool=body["tool"],
            decision="reject",
            arguments=arguments,
        )
        return {
            "status": "rejected",
            "effect": "write",
            "server": body["server"],
            "tool": body["tool"],
            "arguments": arguments,
            "audit_event": event.__dict__,
        }

    result = await call_mcp_tool(body["server"], body["tool"], arguments)
    event = append_audit(
        actor=actor,
        role=role.value,
        phase="executed",
        server=body["server"],
        tool=body["tool"],
        decision=decision,
        arguments=arguments,
    )
    return {
        "status": "completed",
        "effect": "write",
        "server": body["server"],
        "tool": body["tool"],
        "decision": decision,
        "arguments": arguments,
        "result": result,
        "audit_event": event.__dict__,
    }
