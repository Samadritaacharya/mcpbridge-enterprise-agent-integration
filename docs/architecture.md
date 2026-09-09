# Architecture

MCPBridge demonstrates a control plane around Model Context Protocol integrations rather than treating MCP as a thin tool-calling demo.

```text
                         MCPBridge
                            │
                  request / agent intent
                            │
                    deterministic planner
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        GitHub MCP       ITSM MCP      Business MCP
             │              │              │
       tools/resources  tools/resources tools/resources
          /prompts         /prompts        /prompts
             └──────────────┼──────────────┘
                            ▼
                       MCP Client
                            │
                 Tool allowlist + RBAC
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
          READ                           WRITE
             │                             │
        auto execute                 HUMAN REVIEW
                                    /     |      \
                              approve    edit    reject
                                  │        │
                                  └── MCP tool
                                         │
                                         ▼
                                  Hash-linked audit
```

## Protocol assumptions

The project targets MCP Python SDK v2 and protocol revision `2026-07-28`. Modern Streamable HTTP requests are self-contained and do not use protocol-level sessions. The SDK's `Client(server)` in-process transport is used in CI so discovery, schema validation and invocation still pass through the real MCP protocol layer without requiring a network port.

## External MCP surface vs internal domain servers

Three domain servers contain the full synthetic tool catalog. The externally deployable MCP server intentionally publishes only read/advisory tools. Sensitive write tools are invoked by the policy gateway through in-process MCP Clients after approval. This prevents a caller from bypassing the gateway by invoking a public write tool directly.

## LangGraph path

The LangGraph reference is deliberately separate from the stateless production-shaped approval-token path. It proves a real `interrupt()`/resume control flow and executes the MCP tool after authorization. `InMemorySaver` keeps this reference reproducible but not falsely durable.
