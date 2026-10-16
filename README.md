# Connect Hermes Agent to 500+ connectors and 20k+ tools

Hermes can call the Scalekit catalog: 500+ connectors and 20,000+ tools. Scalekit stores each person's token and refreshes it. You paste three Scalekit account values once. You do not paste a Gmail, Slack, or GitHub token into Hermes.

- **500+ connectors. 20,000+ tools.** That is the Scalekit AgentKit catalog published at [scalekit.com](https://www.scalekit.com/). This plugin reaches it with four Hermes tools: `scalekit_list_connections`, `scalekit_authorize`, `scalekit_execute_tool`, and `scalekit_proxy`.
- **A connection is not enough.** The plugin creates a new person id on first launch. That person must approve each app, even when the connection already exists in the dashboard.
- **The approval link is the product.** The first call returns `authorization_link`. You open it. You ask again. The account is then `ACTIVE`.
- **A wrong tool name does not invent data.** Hermes may guess a tool name. The plugin says that tool does not exist. Hermes can then call the app's API through `scalekit_proxy`.
- **Tokens stay in Scalekit.** The chat shows the app's data. It does not show `refresh_token` or `access_token`.

```text
You: Who am I on GitHub? Use the connection github-connect.

Hermes: github-connect is not ACTIVE yet.
        Open this link: https://<your-env>/magicLink/...

# You open the link. The page says "Successfully connected to Github."

You: Who am I on GitHub? Use the connection github-connect.

Hermes: Connection is ACTIVE.
        No tool named github_get_login was found.
        You're signed in on GitHub as <your login>.
```

That second reply is the shape of a live run. The login is the GitHub account you approved. This repository does not ship a sample login.

## Install

You need Hermes, and one finished connection in the [Scalekit dashboard](https://app.scalekit.com). The page is AgentKit, then Connections. Copy the connection name, such as `github-connect`. Do not copy a `conn_` id.

Copy three values from Developers, then Settings, then API Credentials. Keep that page open.

Install from a checkout of this repository:

```bash
hermes plugins install file:///absolute/path/to/hermes-tools
```

Hermes warns that a `file://` URL is local. Continue. Hermes then asks for the three values.

| Prompt | What you paste | Shape |
|---|---|---|
| `SCALEKIT_CLIENT_ID` | Client id | `skc_…` or `prd_skc_…` |
| `SCALEKIT_CLIENT_SECRET` | Client secret | `test_…` |
| `SCALEKIT_ENVIRONMENT_URL` | Environment URL | `https://your-env.scalekit.dev` |

The secret is the Scalekit account secret. It is not a Gmail, Slack, or GitHub token. Hermes saves the three values in `~/.hermes/.env`.

Answer yes when Hermes asks to enable `scalekit`. If it does not ask, run:

```bash
hermes plugins enable scalekit
```

Start a new chat with `hermes`. The first launch creates a person id and prints it once, for example `usr_8f3a2c`. You do not type that id.

> On Hermes 0.19, install the Scalekit Python package into the Hermes Python before the first tool call. That Hermes does not install plugin dependencies. A current Hermes asks to install them during `hermes plugins install`.

```bash
uv pip install --python /path/to/the/hermes/python 'scalekit-sdk-python>=2.12.0,<3'
```

On a mise install of Hermes 0.19.0, that Python is `.../pipx-hermes-agent/0.19.0/hermes-agent/bin/python`. `python -m pip` fails there with `No module named pip`. The error `No module named scalekit` means this package is still missing.

When this repository is public, this also works. Hermes marks it as an unreviewed install:

```bash
hermes plugins install scalekit-inc/hermes-tools
```

After the Hermes catalog lists this plugin, the command is `hermes plugins install scalekit`. That command fails until the listing exists.

## Use it

Stay in one chat.

1. Say `List my Scalekit connections.` Hermes calls `scalekit_list_connections`. You get each connection name, its type, and `COMPLETED`. You do not get a token.
2. Say `Who am I on GitHub? Use the connection github-connect.` Use your real connection name.
3. If the reply contains `authorization_link`, open it. Approve the app. The page says the app is connected.
4. Send the same sentence again. Hermes should say the connection is `ACTIVE`, then return data from the app.

A scheduled job cannot open that link. Approve the app in a normal chat first.

To act as another person for one turn, say the other id in the same sentence, for example `as identifier usr_8f3a2c`. The default remains the id this plugin created.

## When the tool name is missing

Hermes chooses a tool name. Scalekit may not have that name. The plugin returns `No tool named <name> was found.` Hermes can then call `scalekit_proxy` with the app's API path, such as `/user` for GitHub.

The proxy returns JSON or text. A status of 400 or higher is an error and the call stops. If Scalekit returns `TOOL_PROXY_DISABLED`, the catalog does not cover that action. This plugin does not save a file from the proxy.

## What this does not do

- It does not create your Scalekit account.
- It does not create the connection in the dashboard. You create that once, under AgentKit, then Connections.
- It does not install authstack. Authstack is the skill pack for Cursor, Claude Code, Copilot, and Codex.
- It does not change the existing skill `hermes-delegated-auth`.
- It does not register one Hermes tool for every Scalekit action. Four tools cover the catalog.

The rules Hermes reads before a call are in the bundled skill `scalekit:scalekit`.
