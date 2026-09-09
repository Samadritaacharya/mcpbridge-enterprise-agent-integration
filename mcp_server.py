"""Public portfolio-safe MCP surface.

Only read/advisory capabilities are exposed directly over Streamable HTTP. Synthetic write
capabilities live on the domain-specific in-process servers and are reachable through the
MCPBridge REST control plane only after policy + human approval.
"""

from typing import Any

from mcp.server import MCPServer

from src.mcpbridge import systems


def build_public_mcp_server() -> MCPServer:
    mcp = MCPServer(
        "mcpbridge-gateway",
        instructions=(
            "Portfolio-safe enterprise MCP surface. Public tools are read/advisory only; "
            "sensitive writes require the MCPBridge control plane and explicit human approval."
        ),
    )

    @mcp.tool()
    def get_incident(incident_id: str) -> dict[str, Any]:
        """Read a synthetic ITSM incident."""
        return systems.get_incident(incident_id)

    @mcp.tool()
    def get_repository_status(repo: str) -> dict[str, Any]:
        """Read synthetic repository health."""
        return systems.get_repository_status(repo)

    @mcp.tool()
    def compare_suppliers(left: str, right: str) -> dict[str, Any]:
        """Compare two synthetic supplier profiles."""
        return systems.compare_suppliers(left, right)

    @mcp.resource("incident://{incident_id}")
    def incident_resource(incident_id: str) -> str:
        """Incident details as an MCP resource template."""
        return str(systems.get_incident(incident_id))

    @mcp.prompt()
    def change_risk_review(service: str) -> str:
        """Prompt template for evidence-first change-risk review."""
        return (
            f"Review the proposed change for {service}. Separate observable evidence, "
            "risk hypotheses, approval requirements and rollback conditions."
        )

    return mcp


mcp = build_public_mcp_server()
