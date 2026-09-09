# MCPBridge verification record

This file records what is executable and verified. It is intentionally narrower than the README: claims here should correspond to automated checks or directly inspectable code.

## Verified baseline

### Python verification

GitHub Actions job: **Python verification**

The job installs the real project dependencies, including the official MCP Python SDK v2 and LangGraph, then runs:

- Ruff static checks;
- Python compile check;
- the full pytest suite;
- combined ASGI import smoke (`app.py`);
- Docker image build.

The current suite verifies:

1. explicit `(server, tool)` allowlisting and unknown-tool fail-closed behavior;
2. viewer/operator/approver role boundaries;
3. HMAC-bound approval proposal creation, expiry/tamper rejection and role checks;
4. hash-linked audit events and chain validation;
5. deterministic natural-language planning into MCP contracts;
6. real MCP v2 discovery across GitHub, ITSM and Business servers;
7. MCP tools, resources and prompts through the official MCP Client;
8. MCP structured tool results rather than ad-hoc text parsing;
9. automatic execution for read tools;
10. approval-required behavior for write tools;
11. approve, edit and reject write-review paths;
12. LangGraph read execution without interruption;
13. LangGraph `interrupt()` plus same-thread resume before a real MCP write;
14. FastAPI health, catalog, planning and execution contracts;
15. HTTP-level viewer denial, unknown-tool rejection and strict-schema rejection;
16. HTTP-level write proposal -> approve -> MCP execution;
17. HTTP-level edit and reject flows;
18. HTTP-level tampered approval-token rejection;
19. HTTP-level audit-chain inspection;
20. combined ASGI application import and Docker build.

### Web verification

GitHub Actions job: **Web verification**

The job verifies:

- strict TypeScript compilation;
- frontend contract/regression tests;
- production Next.js build.

## Current protocol/runtime targets

- MCP Python SDK: v2 line
- MCP protocol target: `2026-07-28`
- transport: Streamable HTTP
- LangGraph: real `StateGraph` reference path with `interrupt()` / `Command(resume=...)`
- backend: FastAPI / ASGI
- frontend: Next.js 16 / React 19 / TypeScript

## Trust boundary

The public `/mcp` surface is intentionally read/advisory only. Synthetic write tools exist on the domain MCP servers but execute only after the MCPBridge gateway applies allowlist + role policy and a human approves or edits the proposed call.

This prevents the portfolio demo from exposing a write-capable MCP endpoint that would bypass its own approval control plane.

## Explicit limitations

Passing these checks does **not** mean the project is a production enterprise gateway. The current portfolio implementation still uses synthetic systems and demo identities. Production hardening would require OAuth/OIDC, authenticated approver identity, connector-specific credentials, durable replay protection, durable audit storage, tenant isolation, distributed LangGraph checkpoints, rate limiting and production observability.

## Branch protection target

After this verification is green on `main`, protect the default branch with required checks:

- **Python verification**
- **Web verification**

Also require pull requests, require branches to be up to date, require conversation resolution, block force pushes and restrict deletions. For this solo portfolio repository, use `0` required external approvals.
