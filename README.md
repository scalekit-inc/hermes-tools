# Scalekit tools for Hermes

Hermes can act in the apps you connect with Scalekit. Scalekit keeps each person's token and refreshes it. You do not paste a Gmail, Slack, or GitHub token into Hermes.

This is one Hermes plugin. It is not the Scalekit skill pack for Cursor, Claude Code, Copilot, or Codex.

- **Four tools.** Hermes shows `scalekit_list_connections`, `scalekit_authorize`, `scalekit_execute_tool`, and `scalekit_proxy`.
- **Any connector you already created.** Name the connection from AgentKit, then Connections. The plugin does not create that setup.
- **Three Scalekit values.** Copy the client id, client secret, and environment URL from Dashboard, Developers, Settings, API Credentials.
- **Your person id.** The plugin creates it, for example `usr_8f3a2c`, and stores it. You do not type it.
- **Tokens stay in Scalekit.** A tool result does not include a provider refresh token.

```text
You: Who am I on GitHub?

Hermes calls scalekit_execute_tool.
# Before you approve the app:
# {"authorization_link": "https://..."}
# After the account is ACTIVE:
# {"login": "octocat"}
```

The login line shows the shape of a result. It is not a live GitHub call from this repository.

## Install

Create the connection in the [Scalekit dashboard](https://app.scalekit.com) before you ask Hermes to use that app. The page is AgentKit, then Connections.

The catalog command works after this plugin is listed:

```bash
hermes plugins install scalekit
hermes plugins enable scalekit
```

Until that listing exists, install this repository directly. Hermes treats that as an unreviewed install. The repository must be public.

```bash
hermes plugins install scalekit-inc/hermes-tools --no-enable
hermes plugins enable scalekit
```

Install asks for three values. Copy each one from Dashboard, Developers, Settings, API Credentials.

| Prompt | Shape |
|---|---|
| Client id | `skc_1234` |
| Client secret | `test_abcdef1234567890` |
| Environment URL | `https://your-env.scalekit.dev` |

The client secret is the Scalekit account secret. It is not a Gmail or Slack token. The plugin creates the identifier on first load and prints it once.

A missing value stops the plugin and names that value. The plugin does not call Scalekit until all three are set. The plugin stays off until you enable it.

## Use it

1. Ask Hermes which connections exist. It calls `scalekit_list_connections`.
2. Ask Hermes to approve one app. It calls `scalekit_authorize`. Open the `authorization_link` if the account is not `ACTIVE`.
3. Ask Hermes to do the action. It calls `scalekit_execute_tool`.
4. If the connector has no named tool, Hermes calls `scalekit_proxy`. The result is JSON or text. A file download is not saved.

Pass `identifier` only when you want that one call to act as another person. A scheduled run cannot open an approval link. The account must already be `ACTIVE`.

Before the first Scalekit action, Hermes should open the skill `scalekit:scalekit`. That file is the short rule set shipped with this plugin.

## What this does not do

- It does not create a Scalekit account.
- It does not create a connection in the dashboard.
- It does not install authstack.
- It does not replace the existing skill `hermes-delegated-auth`.

Sources: [Connect Hermes to AgentKit](https://docs.scalekit.com/agentkit/hermes/), [Plugin catalog](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog), [Catalog submission](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission).
