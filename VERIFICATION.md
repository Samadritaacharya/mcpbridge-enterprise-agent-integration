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
- a real TCP/Streamable HTTP MCP end-to-end smoke against the mounted `/mcp/` endpoint;
- Docker image build.

At the hardening baseline merged on 9 September 2026, the Python suite contains **41 passing tests** and verifies:

1. explicit `(server, tool)` allowlisting and unknown-tool fail-closed behavior;
2. viewer/operator/approver role boundaries;
3. HMAC-bound approval proposal creation, expiry/tamper rejection and role checks;
4. hash-linked audit events and chain validation;
5. bounded audit retention rollover without breaking retained-chain verification;
6. deterministic natural-language planning into MCP contracts;
7. real MCP v2 discovery across GitHub, ITSM and Business servers;
8. MCP tools, resources and prompts through the official MCP Client;
9. MCP structured tool results rather than ad-hoc text parsing;
10. automatic execution for every allowlisted read tool;
11. approval-required behavior for every allowlisted write tool;
12. approve, edit and reject write-review paths;
13. a ten-tool gateway contract matrix covering the full synthetic allowlist;
14. LangGraph read execution without interruption;
15. LangGraph `interrupt()` plus same-thread resume before a real MCP write;
16. approver-only LangGraph write review with explicit reviewer metadata;
17. FastAPI health, catalog, planning and execution contracts;
18. HTTP-level viewer denial, unknown-tool rejection and strict-schema rejection;
19. HTTP-level write proposal -> approve -> MCP execution;
20. HTTP-level edit and reject flows;
21. HTTP-level tampered approval-token rejection;
22. HTTP-level audit-chain inspection;
23. declared, malformed and actual/chunked request-size enforcement at the 64 KiB boundary;
24. combined ASGI application import;
25. a real Uvicorn server reached over TCP before public MCP verification;
26. MCP protocol negotiation at `2026-07-28` over Streamable HTTP;
27. execution of all three public MCP tools over the real network transport;
28. confirmation that synthetic write tools are absent from the public `/mcp/` surface;
29. public MCP resource-template read and prompt retrieval over the real network transport;
30. Docker image build from the verified commit.

### Web verification

GitHub Actions job: **Web verification**

The job verifies:

- dependency installation with npm audit output;
- strict TypeScript compilation;
- frontend contract/regression tests;
- optimized Next.js production build;
- a real `next start` production-server end-to-end smoke.

The production-server smoke verifies:

1. the portfolio root page renders and contains MCPBridge;
2. `/api/health` reports the expected deterministic demo runtime and protocol target;
3. `/api/catalog` exposes GitHub, ITSM and Business domains;
4. a viewer read executes successfully through `/api/execute`;
5. an operator write returns `approval_required` rather than executing immediately;
6. an approver can complete the reviewed synthetic write through `/api/approve`.

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

## Branch protection

The default branch is protected by the active repository ruleset **Protect main — PR + CI**.

The ruleset requires:

- pull-request based changes to `main`;
- successful **Python verification**;
- successful **Web verification**;
- branches to be up to date before merging;
- conversation resolution;
- deletion protection;
- non-fast-forward / force-push protection.

There are no bypass actors. For this solo portfolio repository, the PR rule uses `0` required external approvals while still forcing changes through the protected pull-request + CI path.
