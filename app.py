"""Combined deployment surface for Vercel, uvicorn and Docker.

Public endpoints:
- /mcp                 official MCP Streamable HTTP endpoint (read/advisory tools only)
- /gateway/health      REST control-plane health
- /gateway/v1/*        catalog, planner, policy execution, approval and audit
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import AsyncIterator

from fastapi import FastAPI
from mcp.server.transport_security import TransportSecuritySettings

from mcp_server import mcp
from src.mcpbridge.api import app as gateway_app


def _transport_security() -> TransportSecuritySettings:
    configured = [
        item.strip()
        for item in os.getenv("MCPBRIDGE_ALLOWED_HOSTS", "*.vercel.app,localhost:*,127.0.0.1:*").split(",")
        if item.strip()
    ]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=configured,
        allowed_origins=[],
    )


mcp_app = mcp.streamable_http_app(
    streamable_http_path="/",
    json_response=True,
    stateless_http=True,
    max_request_body_size=64 * 1024,
    transport_security=_transport_security(),
)


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Mounted ASGI sub-app lifespans do not run automatically; the host owns MCP lifespan.
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="MCPBridge Enterprise Agent Integration Gateway",
    version="0.2.0",
    lifespan=lifespan,
)
app.mount("/gateway", gateway_app)
app.mount("/mcp", mcp_app)


@app.get("/")
def root():
    return {
        "service": "mcpbridge",
        "mcp": "/mcp",
        "gateway_health": "/gateway/health",
        "docs": "/gateway/docs",
        "protocol_target": "2026-07-28",
    }
