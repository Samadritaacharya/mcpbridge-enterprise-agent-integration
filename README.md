# MCPBridge — Enterprise Agent Integration Gateway

[![Python CI](https://github.com/Samadritaacharya/mcpbridge-enterprise-agent-integration/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Samadritaacharya/mcpbridge-enterprise-agent-integration/actions/workflows/python-ci.yml)
[![Web CI](https://github.com/Samadritaacharya/mcpbridge-enterprise-agent-integration/actions/workflows/web-ci.yml/badge.svg)](https://github.com/Samadritaacharya/mcpbridge-enterprise-agent-integration/actions/workflows/web-ci.yml)

> **Give AI agents tools. Keep permissions, human authority and auditability outside the model.**

MCPBridge is a portfolio-scale **enterprise Model Context Protocol integration gateway**. It exposes synthetic GitHub, ITSM and business-system capabilities as MCP **tools, resources and prompts**, consumes them through the official MCP client protocol layer, routes natural-language requests into tool calls, and applies explicit policy before anything can write.

The project is designed to demonstrate MCP as an **integration contract and control-plane problem**, not merely as a decorator around a Python function.

**Stack:** `MCP Python SDK v2` · `LangGraph` · `FastAPI` · `Pydantic` · `Next.js 16` · `React 19` · `TypeScript` · `Docker` · `GitHub Actions`

> All systems and records are synthetic. The repository never mutates a real GitHub, ServiceNow, ERP, procurement or supplier environment.

---

## Why this project exists

An enterprise agent needs more than access to tools. It needs answers to questions such as:

- Which MCP servers may this host trust?
- Which tools may this actor call?
- Which capabilities are read-only and which can create side effects?
- Can an unknown or newly discovered tool execute by default?
- What exact arguments did the agent propose before a human approved them?
- Can a reviewer approve, edit or reject a sensitive write?
- Can the execution be inspected later through an audit trail?
- Can the same architecture expose tools, resources and reusable prompts rather than only tool calls?

MCPBridge makes those controls visible.

---

## Architecture

```text
                         MCPBridge
                            │
                natural-language request
                            │
                  deterministic planner
                            │
                 ┌──────────┼──────────┐
                 ▼          ▼          ▼
             GitHub MCP   ITSM MCP  Business MCP
                 │          │          │
          tools/resources/prompts on each server
                 └──────────┼──────────┘
                            ▼
                    Official MCP Client
                            │
                 fail-closed tool registry
                            │
                    role + effect policy
                            │
                read ───────┴────── write
                 │                     │
                 ▼                     ▼
           auto execution        approval_required
                                       │
                               HUMAN REVIEW
                              /      |       \
                         approve    edit    reject
                            │         │
                            └──── MCP tool call
                                      │
                                      ▼
                              hash-linked audit
```

A separate LangGraph reference path exercises the same policy boundary with a real `StateGraph`, `interrupt()` and same-thread resume before a sensitive MCP tool executes.

---

## MCP surface

| Domain | Tools | Resource template | Prompt |
|---|---|---|---|
| **GitHub MCP** | `search_repository`, `get_repository_status`, `create_github_issue` | `repo://{repo}` | `release_risk_review` |
| **ITSM MCP** | `get_incident`, `create_incident`, `create_change_request` | `incident://{incident_id}` | `incident_analysis` |
| **Business MCP** | `get_supplier`, `compare_suppliers`, `query_purchase_orders`, `generate_decision_pack` | `supplier://{supplier_id}` | `supplier_comparison` |

The externally deployable `/mcp` surface is intentionally **read/advisory only**. Sensitive synthetic write tools stay behind the MCPBridge policy/approval control plane rather than being publicly callable by bypassing the gateway.

---

## Current MCP protocol target

The project targets the official **MCP Python SDK v2** line and protocol revision **`2026-07-28`**.

The modern revision materially changes Streamable HTTP: current requests are self-contained and do not depend on a protocol-level `Mcp-Session-Id`. The SDK still supports older clients, but MCPBridge tests its own v2 server/client connections against the modern protocol by default.

Official references:

- [MCP Python SDK v2](https://github.com/modelcontextprotocol/python-sdk)
- [MCP 2026-07-28 Streamable HTTP](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/streamable-http.mdx)

---

## Policy and human approval

MCPBridge maintains an explicit `(server, tool)` allowlist.

### Roles

| Role | Read tools | Propose writes | Approve writes |
|---|---:|---:|---:|
| `viewer` | ✅ | ❌ | ❌ |
| `operator` | ✅ | ✅ | ❌ |
| `approver` | ✅ | ✅ | ✅ |

Unknown tools fail closed.

Sensitive writes do **not** execute when proposed. The gateway returns `approval_required` plus a short-lived HMAC-signed token bound to the proposed actor, role, MCP server, tool and arguments.

A reviewer can then:

- **approve** — execute the original MCP tool call;
- **edit** — replace the arguments, then execute the reviewed call;
- **reject** — terminate without invoking the MCP write tool.

The public roles are deliberately synthetic demo roles, not a claim of enterprise SSO/RBAC.

---

## Agent request routing

The gateway exposes both direct MCP-contract invocation and natural-language routing.

Example:

```text
"Create a change request for payments-api after the latency incident"
                         │
                         ▼
planner → itsm.create_change_request
                         │
                         ▼
policy → write / approval required
                         │
                         ▼
human approve/edit/reject
                         │
                         ▼
official MCP Client → ITSM MCP tool
```

The deterministic planner is intentional: this project tests integration, authorization and governance without needing a paid model API. A production agent can replace the planner with a model while keeping the same MCP and policy boundaries.

---

## LangGraph HITL reference path

`src/mcpbridge/graph.py` contains a real LangGraph state machine:

```text
START → plan → human_gate → execute MCP tool → END
                     │
                     └── interrupt() for writes
```

Read operations execute without interruption. Write operations stop at `interrupt()`, preserve graph state, and resume the same thread after `approve`, `edit` or `reject`.

The graph uses `InMemorySaver`. That is appropriate for reproducible CI and local architecture verification but is explicitly **not** presented as durable multi-instance production state.

---

## Auditability

Every proposal, rejection and execution can create an event containing:

- actor and demo role;
- MCP server and tool;
- action phase and reviewer decision;
- SHA-256 hash of tool arguments;
- previous event hash;
- current event hash.

The in-process audit implementation serializes appends under a lock and exposes a chain-integrity check. Durable, cross-instance retention belongs in a real database/log platform before enterprise use.

---

## Deployable surfaces

### Python gateway

`app.py` is the combined ASGI deployment surface:

```text
/mcp                 MCP Streamable HTTP (public read/advisory surface)
/gateway/health      control-plane health
/gateway/v1/catalog  discover tools/resources/prompts through MCP clients
/gateway/v1/plan     deterministic request planner
/gateway/v1/agent/run plan + policy + MCP execution/proposal
/gateway/v1/execute  invoke an explicit MCP contract through policy
/gateway/v1/approve  approve/edit/reject a proposed write
/gateway/v1/audit    inspect hash-linked audit events
```

The MCP transport enables DNS-rebinding protection and uses an explicit host allowlist. The default local/portfolio allowlist covers localhost and `*.vercel.app`; production deployments should narrow it to their real hostnames.

### Next.js command center

The frontend shows:

- runtime mode;
- natural-language agent routing;
- explicit MCP contract invocation;
- viewer/operator/approver role switching;
- human approval and editable tool arguments;
- tool/resource/prompt catalog;
- protocol and transport version;
- audit-event hashes;
- control-plane architecture.

With no backend environment variable, the app remains a usable zero-key deterministic portfolio demo. Set `MCPBRIDGE_API_URL` to connect the Next.js server bridge to the deployed Python gateway.

---

## Verification gates

GitHub Actions uses stable branch-protection-ready job names:

### **Python verification**

- Ruff static checks;
- Python compile check;
- policy/RBAC and fail-closed tests;
- HMAC token tamper test;
- hash-linked audit integrity test;
- real in-process MCP client discovery;
- MCP tool/resource/prompt round trip;
- gateway read/write/approve/edit tests;
- LangGraph read execution;
- LangGraph same-thread write interrupt/resume + real MCP execution;
- FastAPI HTTP contract tests;
- combined ASGI import smoke;
- Docker image build.

### **Web verification**

- strict TypeScript;
- public MCP-contract regression tests;
- Next.js production build.

No README quality claim should be treated as stronger than those executable gates.

---

## Repository structure

```text
.
├── app.py                         # combined FastAPI + mounted MCP ASGI surface
├── mcp_server.py                  # public read/advisory MCP server
├── src/mcpbridge/
│   ├── servers.py                 # GitHub / ITSM / Business MCP servers
│   ├── catalog.py                 # real MCP client discovery
│   ├── gateway.py                 # policy-aware MCP execution + approval
│   ├── policy.py                  # allowlist, roles, effects, signed tokens
│   ├── planner.py                 # deterministic request → tool plan
│   ├── graph.py                   # LangGraph interrupt/resume reference
│   ├── audit.py                   # hash-linked audit events
│   ├── systems.py                 # synthetic integration implementations
│   └── api.py                     # REST control plane
├── frontend/                      # Next.js command center
├── tests/                         # unit + MCP + gateway + LangGraph tests
├── docs/                          # architecture, security, deployment, interview guide
├── Dockerfile
└── .github/workflows/
```

---

## Run locally

### Python

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
pytest
uvicorn app:app --reload
```

Then inspect:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/gateway/docs
http://127.0.0.1:8000/mcp
```

### Frontend

```bash
cd frontend
npm install
npm run typecheck
npm run test:web
npm run build
npm run dev
```

Connected mode:

```bash
MCPBRIDGE_API_URL=http://127.0.0.1:8000/gateway npm run dev
```

### Docker

```bash
docker build -t mcpbridge .
docker run --rm -p 8000:8000 \
  -e MCPBRIDGE_APPROVAL_SECRET='replace-me' \
  mcpbridge
```

---

## Security boundaries

Implemented portfolio controls include:

- explicit server/tool allowlist;
- read/write effect classification;
- viewer/operator/approver policy;
- unknown-tool fail closed;
- human approval for synthetic writes;
- HMAC tamper detection and expiry;
- strict request schemas;
- 64 KiB request-size boundary;
- public MCP surface excludes write tools;
- MCP transport host allowlist / DNS-rebinding protection;
- tamper-evident in-memory audit chain;
- synthetic data only.

Production gaps are equally explicit: OAuth/OIDC, authenticated approver identity, durable replay protection, durable audit storage, connector-specific credentials, rate limiting, tenant isolation, distributed LangGraph checkpoints and enterprise observability.

See [`docs/security.md`](docs/security.md).

---

## Interview / CV positioning

The point of MCPBridge is **not** “I know how to decorate a Python function as an MCP tool.”

The project demonstrates:

> **MCP standardizes the capability contract. The enterprise gateway still owns trust, authorization, human approval and auditability.**

Suggested CV bullet after CI/deployment verification:

> **MCPBridge — Enterprise Agent Integration Gateway:** Built a multi-domain MCP server/client gateway across synthetic GitHub, ITSM and business systems with tools/resources/prompts, Streamable HTTP, fail-closed role policy, human-approved writes, LangGraph HITL orchestration and tamper-evident audit trails.

See [`docs/interview-guide.md`](docs/interview-guide.md) for design reasoning and likely technical-interview questions.

---

## Status

**Implementation:** built on a feature branch and validated through CI before merge.  
**Live app:** added only after Vercel deployment and external smoke verification.  
**Production integrations:** intentionally synthetic; no claim of real enterprise system access.
