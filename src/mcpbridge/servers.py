from __future__ import annotations

from mcp.server import MCPServer

from . import systems


def build_github_server() -> MCPServer:
    mcp = MCPServer("mcpbridge-github", instructions="Synthetic GitHub connector. Read tools are safe; write tools are invoked only after gateway approval.")

    @mcp.tool()
    def search_repository(query: str) -> list[dict]:
        """Search synthetic repository metadata."""
        return systems.search_repository(query)

    @mcp.tool()
    def get_repository_status(repo: str) -> dict:
        """Get CI, issue, PR and deployment status for a synthetic repository."""
        return systems.get_repository_status(repo)

    @mcp.tool()
    def create_github_issue(repo: str, title: str, body: str, severity: str = "medium") -> dict:
        """Create a synthetic GitHub issue. MCPBridge policy must approve before calling this write tool."""
        return systems.create_github_issue(repo, title, body, severity)

    @mcp.resource("repo://{repo}")
    def repository_resource(repo: str) -> str:
        """Repository status as an MCP resource."""
        return str(systems.get_repository_status(repo))

    @mcp.prompt()
    def release_risk_review(repo: str) -> str:
        """Prompt template for release-risk review."""
        return f"Review repository {repo} for CI, open-work, deployment and operational risk. Separate evidence from recommendation."

    return mcp


def build_itsm_server() -> MCPServer:
    mcp = MCPServer("mcpbridge-itsm", instructions="Synthetic ITSM connector with governed write operations.")

    @mcp.tool()
    def get_incident(incident_id: str) -> dict:
        """Read a synthetic incident."""
        return systems.get_incident(incident_id)

    @mcp.tool()
    def create_incident(title: str, service: str, severity: str, summary: str) -> dict:
        """Create a synthetic incident after explicit gateway approval."""
        return systems.create_incident(title, service, severity, summary)

    @mcp.tool()
    def create_change_request(service: str, summary: str, risk: str, implementation_window: str) -> dict:
        """Create a synthetic change request after explicit gateway approval."""
        return systems.create_change_request(service, summary, risk, implementation_window)

    @mcp.resource("incident://{incident_id}")
    def incident_resource(incident_id: str) -> str:
        """Incident details as an MCP resource."""
        return str(systems.get_incident(incident_id))

    @mcp.prompt()
    def incident_analysis(incident_id: str) -> str:
        """Prompt template for evidence-first incident analysis."""
        return f"Analyze {incident_id}. Cite observable evidence, separate hypotheses, propose safe next actions, and do not execute writes without approval."

    return mcp


def build_business_server() -> MCPServer:
    mcp = MCPServer("mcpbridge-business", instructions="Synthetic supplier and purchase-order data for portfolio-safe enterprise workflows.")

    @mcp.tool()
    def get_supplier(supplier_id: str) -> dict:
        """Read a synthetic supplier profile."""
        return systems.get_supplier(supplier_id)

    @mcp.tool()
    def compare_suppliers(left: str, right: str) -> dict:
        """Compare two synthetic suppliers."""
        return systems.compare_suppliers(left, right)

    @mcp.tool()
    def query_purchase_orders(supplier_id: str) -> list[dict]:
        """Read synthetic purchase-order data."""
        return systems.query_purchase_orders(supplier_id)

    @mcp.tool()
    def generate_decision_pack(question: str) -> dict:
        """Generate an advisory, evidence-backed decision pack."""
        return systems.generate_decision_pack(question)

    @mcp.resource("supplier://{supplier_id}")
    def supplier_resource(supplier_id: str) -> str:
        """Supplier record as an MCP resource."""
        return str(systems.get_supplier(supplier_id))

    @mcp.prompt()
    def supplier_comparison(left: str = "SUP-ALPHA", right: str = "SUP-BETA") -> str:
        """Prompt template for supplier comparison."""
        return f"Compare {left} and {right} on cost, lead time, warranty, security-update coverage and risk. State trade-offs explicitly."

    return mcp


def build_servers() -> dict[str, MCPServer]:
    return {"github": build_github_server(), "itsm": build_itsm_server(), "business": build_business_server()}
