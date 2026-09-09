from __future__ import annotations

from typing import Any

from mcp import Client

from .policy import POLICIES
from .servers import build_servers


async def discover_catalog() -> dict[str, Any]:
    """Discover tools/resources/prompts through real in-process MCP clients."""

    servers = build_servers()
    result: dict[str, Any] = {
        "protocol_target": "2026-07-28",
        "transport": "Streamable HTTP",
        "servers": {},
    }
    discovered_names: set[str] = set()

    for name, server in servers.items():
        async with Client(server, raise_exceptions=True) as client:
            tools = await client.list_tools()
            resources = await client.list_resource_templates()
            prompts = await client.list_prompts()

            server_tools = []
            for tool in tools.tools:
                qualified = f"{name}.{tool.name}"
                if qualified in discovered_names:
                    raise RuntimeError(f"duplicate qualified MCP tool: {qualified}")
                discovered_names.add(qualified)
                policy = POLICIES.get((name, tool.name))
                if policy is None:
                    raise RuntimeError(f"MCP tool has no fail-closed policy: {qualified}")
                server_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.input_schema,
                        "policy": policy.to_dict(),
                    }
                )

            result["servers"][name] = {
                "protocol_version": str(client.protocol_version),
                "tools": server_tools,
                "resources": [
                    {
                        "uri_template": str(item.uri_template),
                        "name": item.name,
                        "description": item.description or "",
                    }
                    for item in resources.resource_templates
                ],
                "prompts": [
                    {"name": item.name, "description": item.description or ""}
                    for item in prompts.prompts
                ],
            }
    return result
