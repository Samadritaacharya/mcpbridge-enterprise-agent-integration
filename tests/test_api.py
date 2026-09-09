import pytest
from httpx import ASGITransport, AsyncClient

from src.mcpbridge.api import app


@pytest.mark.asyncio
async def test_gateway_http_contracts():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["protocol_target"] == "2026-07-28"

        catalog = await client.get("/v1/catalog")
        assert catalog.status_code == 200
        assert set(catalog.json()["servers"]) == {"github", "itsm", "business"}

        read = await client.post(
            "/v1/execute",
            headers={"x-demo-role": "viewer"},
            json={"server": "itsm", "tool": "get_incident", "arguments": {"incident_id": "INC-428"}},
        )
        assert read.status_code == 200
        assert read.json()["status"] == "completed"

        denied = await client.post(
            "/v1/execute",
            headers={"x-demo-role": "viewer"},
            json={
                "server": "itsm",
                "tool": "create_change_request",
                "arguments": {
                    "service": "payments-api",
                    "summary": "x",
                    "risk": "medium",
                    "implementation_window": "later",
                },
            },
        )
        assert denied.status_code == 403

        unknown = await client.post(
            "/v1/execute",
            json={"server": "itsm", "tool": "delete_everything", "arguments": {}},
        )
        assert unknown.status_code == 422
