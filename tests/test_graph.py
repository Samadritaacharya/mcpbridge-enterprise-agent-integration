import pytest
from langgraph.types import Command

from src.mcpbridge.graph import build_graph


@pytest.mark.asyncio
async def test_langgraph_read_executes_without_interrupt():
    graph = build_graph()
    result = await graph.ainvoke(
        {"request": "Show incident INC-428", "actor": "viewer-a", "role": "viewer"},
        config={"configurable": {"thread_id": "read-thread"}},
    )
    assert result["status"] == "completed"
    assert result["tool"] == "get_incident"
    assert result["result"]["id"] == "INC-428"


@pytest.mark.asyncio
async def test_langgraph_interrupt_resume_and_real_mcp_write():
    graph = build_graph()
    config = {"configurable": {"thread_id": "write-thread"}}
    first = await graph.ainvoke(
        {
            "request": "Create a change request for payments-api",
            "actor": "operator-a",
            "role": "operator",
        },
        config=config,
    )
    assert "__interrupt__" in first
    resumed = await graph.ainvoke(
        Command(
            resume={
                "decision": "approve",
                "reviewer_role": "approver",
                "reviewer_actor": "approver-a",
            }
        ),
        config=config,
    )
    assert resumed["status"] == "completed"
    assert resumed["approval"]["reviewer_actor"] == "approver-a"
    assert resumed["result"]["status"] == "created"


@pytest.mark.asyncio
async def test_langgraph_non_approver_cannot_resume_sensitive_write():
    graph = build_graph()
    config = {"configurable": {"thread_id": "unauthorized-write-thread"}}
    first = await graph.ainvoke(
        {
            "request": "Create a change request for payments-api",
            "actor": "operator-a",
            "role": "operator",
        },
        config=config,
    )
    assert "__interrupt__" in first

    with pytest.raises(PermissionError, match="only the approver role"):
        await graph.ainvoke(
            Command(
                resume={
                    "decision": "approve",
                    "reviewer_role": "operator",
                    "reviewer_actor": "operator-a",
                }
            ),
            config=config,
        )


@pytest.mark.asyncio
async def test_langgraph_reject_stops_before_tool_execution():
    graph = build_graph()
    config = {"configurable": {"thread_id": "reject-thread"}}
    first = await graph.ainvoke(
        {
            "request": "Create a GitHub issue for payments-api",
            "actor": "operator-a",
            "role": "operator",
        },
        config=config,
    )
    assert "__interrupt__" in first
    resumed = await graph.ainvoke(
        Command(
            resume={
                "decision": "reject",
                "reviewer_role": "approver",
                "reviewer_actor": "approver-b",
            }
        ),
        config=config,
    )
    assert resumed["status"] == "rejected"
    assert "result" not in resumed
