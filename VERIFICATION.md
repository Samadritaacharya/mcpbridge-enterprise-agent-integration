# Verification

MCPBridge treats CI output as the source of truth for engineering claims.

## Required checks

- **Python verification** — policy, audit, MCP protocol integration, gateway, LangGraph, HTTP contracts, ASGI import and Docker build.
- **Web verification** — strict TypeScript, contract regression tests and Next.js production build.

This file is updated after the first clean CI run with the exact observed results. Live deployment claims are added only after external production smoke verification.
