import pytest
from mcp import Client
from mcp.types import TextResourceContents

from src.mcpbridge.servers import (
    build_business_server,
    build_github_server,
    build_itsm_server,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "builder,expected",
    [
        (
            build_github_server,
            {"search_repository", "get_repository_status", "create_github_issue"},
        ),
        (
            build_itsm_server,
            {"get_incident", "create_incident", "create_change_request"},
        ),
        (
            build_business_server,
            {
                "get_supplier",
                "compare_suppliers",
                "query_purchase_orders",
                "generate_decision_pack",
            },
        ),
    ],
)
async def test_real_mcp_discovery(builder, expected):
    async with Client(builder(), raise_exceptions=True) as client:
        tools = await client.list_tools()
        assert expected.issubset({item.name for item in tools.tools})
        assert str(client.protocol_version) == "2026-07-28"
        assert (await client.list_resource_templates()).resource_templates
        assert (await client.list_prompts()).prompts


@pytest.mark.asyncio
async def test_real_mcp_tool_resource_and_prompt_round_trip():
    async with Client(build_itsm_server(), raise_exceptions=True) as client:
        result = await client.call_tool("get_incident", {"incident_id": "INC-428"})
        assert result.is_error is False
        assert result.structured_content["id"] == "INC-428"

        resource = await client.read_resource("incident://INC-428")
        assert isinstance(resource.contents[0], TextResourceContents)
        assert "INC-428" in resource.contents[0].text

        prompt = await client.get_prompt("incident_analysis", {"incident_id": "INC-428"})
        assert prompt.messages
