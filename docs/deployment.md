# Deployment

MCPBridge is designed as two independently deployable portfolio surfaces from one GitHub repository.

## 1. Frontend project

Import the repository into Vercel with:

- Project name: `mcpbridge-enterprise-agent-integration-web`
- Root Directory: `frontend`
- Framework: Next.js
- Build command: default / `npm run build`
- Output: default / `.next`
- Install: default / `npm install`

No environment variable is required for the zero-key fallback.

Once the Python gateway is hosted, set:

```text
MCPBRIDGE_API_URL=https://<backend-host>/gateway
NEXT_PUBLIC_SITE_URL=https://<frontend-host>
```

and redeploy.

## 2. Python gateway project

Import the repository root as a FastAPI project. `app.py` exports the combined ASGI application and is the production entrypoint.

Configure:

```text
MCPBRIDGE_ENV=production
MCPBRIDGE_APPROVAL_SECRET=<long-random-secret>
MCPBRIDGE_ALLOWED_HOSTS=<backend-host>,*.vercel.app
```

The public endpoints are:

- `/mcp` — official MCP Streamable HTTP read/advisory surface
- `/gateway/health`
- `/gateway/v1/catalog`
- `/gateway/v1/plan`
- `/gateway/v1/agent/run`
- `/gateway/v1/execute`
- `/gateway/v1/approve`
- `/gateway/v1/audit`

## Why the host allowlist matters

The MCP Python SDK's Streamable HTTP transport includes DNS-rebinding protection. MCPBridge passes an explicit host allowlist rather than disabling that boundary for deployment convenience.

## Stateful caveat

The public gateway approval flow is based on a signed, expiring proposal token and therefore does not depend on a sticky LangGraph process. The separate LangGraph reference uses `InMemorySaver`; do not present that path as durable across serverless instances until a persistent checkpointer is added.
