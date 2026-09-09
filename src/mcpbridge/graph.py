from __future__ import annotations

from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .gateway import call_mcp_tool
from .models import Role
from .planner import plan_request
from .policy import authorize


class AgentState(TypedDict, total=False):
    request: str
    actor: str
    role: str
    server: str
    tool: str
    arguments: dict[str, Any]
    reason: str
    effect: str
    approval: dict[str, Any]
    status: str
    result: Any


def build_graph():
    """Build the reference LangGraph orchestration path.

    Read tools pass straight through the gate and execute. Sensitive writes interrupt the
    graph, then resume the exact thread only after an explicit synthetic approver decision.
    The resume payload carries reviewer role/actor metadata so the reference graph exercises
    the same separation-of-duties boundary as the REST control plane. This is still demo
    identity, not enterprise SSO/OIDC.

    The graph intentionally uses InMemorySaver and is therefore a local/CI reference rather
    than a claim of durable multi-instance production state.
    """

    def plan(state: AgentState) -> dict[str, Any]:
        call = plan_request(state["request"])
        policy = authorize(Role(state.get("role", Role.OPERATOR.value)), call.server, call.tool)
        return {
            "server": call.server,
            "tool": call.tool,
            "arguments": call.arguments,
            "reason": call.reason,
            "effect": policy.effect.value,
        }

    def human_gate(state: AgentState) -> dict[str, Any]:
        policy = authorize(
            Role(state.get("role", Role.OPERATOR.value)), state["server"], state["tool"]
        )
        if not policy.approval_required:
            return {"status": "authorized_read"}

        raw = interrupt(
            {
                "type": "mcp_write_approval",
                "server": state["server"],
                "tool": state["tool"],
                "arguments": state["arguments"],
                "allowed": ["approve", "edit", "reject"],
                "required_reviewer_role": Role.APPROVER.value,
            }
        )
        if not isinstance(raw, dict):
            raise ValueError("write review must include decision and reviewer metadata")

        choice = raw.get("decision")
        if choice not in {"approve", "edit", "reject"}:
            raise ValueError("human decision must be approve, edit or reject")
        if raw.get("reviewer_role") != Role.APPROVER.value:
            raise PermissionError("only the approver role can review MCP write execution")
        reviewer_actor = raw.get("reviewer_actor")
        if not isinstance(reviewer_actor, str) or not reviewer_actor.strip():
            raise ValueError("reviewer_actor is required for write review")

        decision = dict(raw)
        decision["reviewer_actor"] = reviewer_actor.strip()
        update: dict[str, Any] = {
            "approval": decision,
            "status": "rejected" if choice == "reject" else "authorized_write",
        }
        if choice == "edit":
            edited = decision.get("arguments")
            if not isinstance(edited, dict):
                raise ValueError("edit decision requires replacement arguments")
            update["arguments"] = edited
        return update

    async def execute_tool(state: AgentState) -> dict[str, Any]:
        result = await call_mcp_tool(state["server"], state["tool"], state["arguments"])
        return {"result": result, "status": "completed"}

    def route_after_gate(state: AgentState) -> str:
        return "end" if state.get("status") == "rejected" else "execute"

    graph = StateGraph(AgentState)
    graph.add_node("plan", plan)
    graph.add_node("human_gate", human_gate)
    graph.add_node("execute", execute_tool)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "human_gate")
    graph.add_conditional_edges(
        "human_gate",
        route_after_gate,
        {"execute": "execute", "end": END},
    )
    graph.add_edge("execute", END)
    return graph.compile(checkpointer=InMemorySaver())
