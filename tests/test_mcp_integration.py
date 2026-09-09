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
@pytest.mark.parametrize(
    "builder,tool,arguments,resource_uri,resource_marker,prompt,prompt_arguments",
    [
        (
            build_github_server,
            "get_repository_status",
            {"repo": "payments-api"},
            "repo://payments-api",
            "payments-api",
            "release_risk_review",
            {"repo": "payments-api"},
        ),
        (
            build_itsm_server,
            "get_incident",
            {"incident_id": "INC-428"},
            "incident://INC-428",
            "INC-428",
            "incident_analysis",
            {"incident_id": "INC-428"},
        ),
        (
            build_business_server,
            "get_supplier",
            {"supplier_id": "SUP-ALPHA"},
            "supplier://SUP-ALPHA",
            "SUP-ALPHA",
            "supplier_comparison",
            {"left": "SUP-ALPHA", "right": "SUP-BETA"},
        ),
    ],
)
async def test_each_domain_tool_resource_and_prompt_round_trip(
    builder,
    tool,
    arguments,
    resource_uri,
    resource_marker,
    prompt,
    prompt_arguments,
):
    async with Client(builder(), raise_exceptions=True) as client:
        result = await client.call_tool(tool, arguments)
        assert result.is_error is False
        assert result.structured_content is not None

        resource = await client.read_resource(resource_uri)
        assert isinstance(resource.contents[0], TextResourceContents)
        assert resource_marker in resource.contents[0].text

        prompt_result = await client.get_prompt(prompt, prompt_arguments)
        assert prompt_result.messages
