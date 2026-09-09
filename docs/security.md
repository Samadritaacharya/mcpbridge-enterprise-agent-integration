# Security and trust boundaries

MCPBridge is a portfolio-scale reference implementation using synthetic data. It is intentionally designed to show **where trust should live** rather than hide security assumptions behind agent autonomy.

## Implemented controls

- explicit allowlist of MCP server + tool pairs
- read/write effect classification
- viewer/operator/approver demo roles
- unknown tools fail closed
- human approval required for write effects
- HMAC-signed approval token bound to the proposed server/tool/arguments and expiry
- edited write arguments must be supplied explicitly and are re-used for the executed MCP call
- public `/mcp` surface exposes read/advisory tools only
- strict Pydantic request models and strict Next.js request validation
- 64 KiB HTTP request-size guard
- MCP Streamable HTTP DNS-rebinding protection with explicit host allowlist
- hash-linked audit events with in-process chain verification
- synthetic systems and portfolio-safe data only

## Important limitations

- demo roles are caller-supplied headers, not authenticated enterprise identities
- the HMAC proposal token is tamper-evident but the demo does not provide durable distributed one-time-token replay storage
- audit storage is in memory and therefore not durable across function instances
- no OAuth resource-server configuration is enabled in the public demo
- no tenant isolation or connector-specific ACL model
- LangGraph reference state uses `InMemorySaver`
- no rate limiter or WAF policy is implemented in application code
- no real GitHub, ServiceNow, ERP or procurement credential is used

## Production evolution

A real enterprise deployment should add OAuth/OIDC, service-to-service authentication, authenticated approver identity, durable audit/replay storage, per-tool least-privilege connector credentials, tenant and resource ACLs, rate limits, secret rotation, OpenTelemetry/SIEM export, persistent LangGraph checkpoints and security tests for prompt/tool-injection scenarios.
