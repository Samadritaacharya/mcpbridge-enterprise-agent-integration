from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .audit import list_audit, verify_audit_chain
from .catalog import discover_catalog
from .gateway import decide, execute
from .models import Role
from .planner import plan_request

app = FastAPI(title="MCPBridge REST Control Plane", version="0.2.0")
MAX_BODY_BYTES = 64 * 1024


@app.middleware("http")
async def request_size_guard(request: Request, call_next):
    value = request.headers.get("content-length")
    if value and int(value) > MAX_BODY_BYTES:
        return JSONResponse({"detail": "request body too large"}, status_code=413)
    return await call_next(request)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExecuteRequest(StrictModel):
    server: str = Field(min_length=2, max_length=40)
    tool: str = Field(min_length=2, max_length=80)
    arguments: dict[str, Any] = Field(default_factory=dict)


class PlanRequest(StrictModel):
    request: str = Field(min_length=5, max_length=2000)


class DecisionRequest(StrictModel):
    approval_token: str = Field(min_length=20, max_length=12000)
    decision: Literal["approve", "edit", "reject"]
    edited_arguments: dict[str, Any] | None = None


def _role(value: str) -> Role:
    try:
        return Role(value)
    except ValueError as exc:
        raise HTTPException(422, "x-demo-role must be viewer, operator or approver") from exc


def _actor(value: str) -> str:
    clean = value.strip()
    if not 1 <= len(clean) <= 120:
        raise HTTPException(422, "x-demo-actor must contain 1-120 characters")
    return clean


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "mcpbridge",
        "mcp_sdk_target": "v2",
        "protocol_target": "2026-07-28",
        "transport": "streamable-http",
        "live_mode": "synthetic-enterprise-demo",
        "langgraph_reference": True,
        "state_boundary": (
            "approval token is stateless; LangGraph reference checkpointer is in-memory"
        ),
        "controls": [
            "tool-allowlist",
            "role-policy",
            "human-write-approval",
            "schema-validation",
            "hash-linked-audit",
        ],
        "deployment_sha": os.getenv(
            "VERCEL_GIT_COMMIT_SHA", os.getenv("GITHUB_SHA", "local")
        ),
    }


@app.get("/v1/catalog")
async def catalog():
    return await discover_catalog()


@app.post("/v1/plan")
def plan(body: PlanRequest):
    return plan_request(body.request).__dict__


@app.post("/v1/agent/run")
async def agent_run(
    body: PlanRequest,
    x_demo_actor: str = Header(default="portfolio-user"),
    x_demo_role: str = Header(default="operator"),
):
    call = plan_request(body.request)
    outcome = await execute(
        actor=_actor(x_demo_actor),
        role=_role(x_demo_role),
        server=call.server,
        tool=call.tool,
        arguments=call.arguments,
    )
    return {"plan": call.__dict__, **outcome}


@app.post("/v1/execute")
async def execute_route(
    body: ExecuteRequest,
    x_demo_actor: str = Header(default="portfolio-user"),
    x_demo_role: str = Header(default="operator"),
):
    try:
        return await execute(
            actor=_actor(x_demo_actor),
            role=_role(x_demo_role),
            server=body.server,
            tool=body.tool,
            arguments=body.arguments,
        )
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/v1/approve")
async def approve_route(
    body: DecisionRequest,
    x_demo_actor: str = Header(default="portfolio-approver"),
    x_demo_role: str = Header(default="approver"),
):
    try:
        return await decide(
            actor=_actor(x_demo_actor),
            role=_role(x_demo_role),
            approval_token=body.approval_token,
            decision=body.decision,
            edited_arguments=body.edited_arguments,
        )
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/v1/audit")
def audit(limit: int = 50):
    return {
        "events": list_audit(limit),
        "chain_valid": verify_audit_chain(),
        "persistence": "in-memory-demo",
    }
