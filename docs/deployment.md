# Deployment

MCPBridge is designed as two independently deployable portfolio surfaces from one GitHub repository.

## Deployment readiness model

There are two valid live-app modes:

1. **Frontend-only public demo** — deploy the `frontend` project to Vercel with no backend environment variable. This mode is zero-key, deterministic, interactive and portfolio-safe.
2. **Connected full-stack demo** — deploy the Python FastAPI/MCP gateway as a second Vercel project, then point the frontend server bridge at it with `MCPBRIDGE_API_URL`.

GitHub Actions verifies both the standalone frontend production server and the connected Next.js -> Python gateway -> MCP path before deployment.

## 1. Frontend project

Import the repository into Vercel with:

- Project name: `mcpbridge-enterprise-agent-integration-web`
- Root Directory: `frontend`
- Framework: Next.js
- Build command: default / `npm run build`
- Output: default / `.next`
- Install: default / `npm install`

No environment variable is required for the zero-key fallback.

Optional hardening for the public synthetic approval-token demo:

```text
MCPBRIDGE_DEMO_SECRET=<long-random-secret>
```

This does not turn demo roles into real authentication; it only replaces the portfolio fallback signing secret.

Once the Python gateway is hosted, set:

```text
MCPBRIDGE_API_URL=https://<backend-host>/gateway
NEXT_PUBLIC_SITE_URL=https://<frontend-host>
```

and redeploy.

## 2. Python gateway project

Import the repository root as a second Vercel project.

The repository now makes the backend deployment contract explicit in two places:

- `pyproject.toml` declares `[tool.vercel] entrypoint = "app:app"`;
- root `vercel.json` selects the FastAPI framework, configures the `app.py` function and excludes frontend/test/docs files from the Python function bundle.

Configure:

```text
MCPBRIDGE_ENV=production
MCPBRIDGE_APPROVAL_SECRET=<long-random-secret>
MCPBRIDGE_ALLOWED_HOSTS=<backend-host>,*.vercel.app
```

For the first preview deployment, `*.vercel.app` is sufficient. After the final production hostname is known, prefer narrowing `MCPBRIDGE_ALLOWED_HOSTS` to the exact backend hostname plus any intentional preview hostname pattern.

The public endpoints are:

- `/mcp` — official MCP Streamable HTTP read/advisory surface
- `/gateway/health`
- `/gateway/v1/catalog`
- `/gateway/v1/plan`
- `/gateway/v1/agent/run`
- `/gateway/v1/execute`
- `/gateway/v1/approve`
- `/gateway/v1/audit`

## Pre-production gate

Before promoting the Vercel deployment to the portfolio URL, verify:

- GitHub **Python verification** is green on the deployed commit;
- GitHub **Web verification** is green on the deployed commit;
- the Web verification connected-mode smoke passes Next.js -> Python gateway -> MCP read + governed write + audit;
- the Vercel build completes without framework-detection or bundle errors;
- `/api/health` returns the expected deployment SHA and runtime mode;
- the homepage loads anonymously;
- a read workflow completes;
- an operator write is blocked with `approval_required`;
- an approver can approve the synthetic write;
- connected mode, if enabled, reports `connected-python-mcp`.

Only after those checks should the README status be changed from “Live app: added only after Vercel deployment and external smoke verification” to a real public URL.

## Why the host allowlist matters

The MCP Python SDK's Streamable HTTP transport includes DNS-rebinding protection. MCPBridge passes an explicit host allowlist rather than disabling that boundary for deployment convenience.

## Stateful caveat

The public gateway approval flow is based on a signed, expiring proposal token and therefore does not depend on a sticky LangGraph process. The separate LangGraph reference uses `InMemorySaver`; do not present that path as durable across serverless instances until a persistent checkpointer is added.

The hash-linked audit log is also intentionally in-memory. On serverless infrastructure, different requests may reach different warm instances, so connected-mode audit history is demonstrative rather than durable. Durable audit retention belongs in a database/log platform before any production-enterprise claim.
