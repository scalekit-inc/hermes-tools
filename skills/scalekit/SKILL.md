---
name: scalekit
description: >
  Use when Hermes must act in an app through Scalekit.
  Open this skill before the first Scalekit tool call.
version: 0.1.0
author: Scalekit Inc
---

# Scalekit tools for Hermes

Hermes is the host. Scalekit holds the tokens. The plugin creates the identifier and stores it. Do not invent a client id, client secret, or environment URL.

## Guardrails

- Provider tokens stay in Scalekit. Do not write a Gmail, Slack, or Calendar token to disk.
- Do not run `hermes mcp login` against Scalekit.
- Do not mint a Virtual MCP session token on this host.
- The Slack gateway bot is not the person whose connected account is active.
- A scheduled run cannot open an authorization link. The connected account must already be ACTIVE.
- Use the connection name from AgentKit, Connections. Do not use a `conn_` id.

## Approve an app

Call `scalekit_authorize` with the connection name. Open this skill as `scalekit:scalekit` before that call.

- If the result is an error, the connection is missing or unfinished. Tell the standing assistant to finish it in the Scalekit dashboard. Stop.
- If the result has `authorization_link`, show that link. Do not call another Scalekit tool until the account is ACTIVE.
- If the result is `{"status": "ACTIVE"}`, the person has already approved the app.

Pass `identifier` only when the standing assistant names another person for this turn.
