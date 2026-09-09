from src.mcpbridge.planner import plan_request


def test_read_request_routes_to_itsm():
    plan = plan_request("Show me incident INC-428 and its current status")
    assert (plan.server, plan.tool) == ("itsm", "get_incident")


def test_write_request_routes_to_sensitive_tool():
    plan = plan_request("Create a change request for the payments API after the latency incident")
    assert (plan.server, plan.tool) == ("itsm", "create_change_request")
