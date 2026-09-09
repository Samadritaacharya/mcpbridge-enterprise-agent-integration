# Interview guide

## 30-second explanation

MCPBridge is an enterprise agent integration gateway built around real MCP servers and clients. Three synthetic domains publish tools, resource templates and prompts. A gateway discovers and invokes those capabilities through the MCP protocol, applies a fail-closed server/tool allowlist and role policy, automatically executes reads, and turns writes into human-review proposals. A separate LangGraph path uses a real interrupt and same-thread resume before an approved MCP write executes. The UI exposes the catalog, permissions, proposed arguments and hash-linked audit trail.

## Why MCP instead of direct API wrappers?

MCP standardizes how hosts discover and invoke capabilities. That reduces integration-specific coupling, but MCP itself is not an authorization strategy. MCPBridge intentionally keeps policy, reviewer authority and audit outside the model and outside the individual tool's natural-language description.

## Why is the public MCP endpoint read-only?

If a sensitive write tool were directly exposed over the same unauthenticated public MCP surface, a caller could bypass the REST policy gateway. The public server therefore demonstrates MCP interoperability with safe read/advisory tools, while the full domain write servers are invoked internally after policy + approval.

## Why use signed approval tokens?

The deployed portfolio path should not depend on sticky in-memory graph state just to preserve the exact proposed call. The token binds the proposed server, tool and arguments with an expiry and tamper check. In a real enterprise system the proposal/replay state would also be persisted durably and bound to authenticated identities.

## Where does LangGraph fit?

LangGraph demonstrates agent state and true human-in-the-loop orchestration. The graph plans, checks policy, interrupts before a write, resumes the same thread and then performs the real MCP call. The project does not pretend `InMemorySaver` is durable across serverless replicas.

## Why protocol revision 2026-07-28?

The current MCP v2 line uses the modern request model where Streamable HTTP no longer depends on protocol-level sessions. That matters for horizontally scaled gateway architecture. The SDK still supports earlier clients, but MCPBridge's CI expects modern negotiation for its own v2 servers.

## CV bullet

**MCPBridge — Enterprise Agent Integration Gateway:** Built a multi-domain MCP server/client gateway across synthetic GitHub, ITSM and business systems with tools/resources/prompts, Streamable HTTP, fail-closed role policy, human-approved writes, LangGraph HITL orchestration and tamper-evident audit trails.

## LinkedIn project description

Designed and built an enterprise AI integration gateway demonstrating Model Context Protocol architecture beyond basic tool calling. Implemented separate synthetic GitHub, ITSM and business MCP servers, official MCP client discovery/invocation, tools/resources/prompts, read-vs-write policy, viewer/operator/approver permissions, HMAC-bound approval proposals, editable human-reviewed writes, hash-linked audit events, LangGraph HITL execution, FastAPI contracts, Next.js command-center UX, Docker and CI.
