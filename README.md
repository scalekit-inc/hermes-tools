# Connect Hermes Agent to 500+ connectors and 20k+ tools

Hermes can call the Scalekit catalog: 500+ connectors and 20,000+ tools, as published on [scalekit.com](https://www.scalekit.com/). Scalekit stores each person's token and refreshes it. You paste three Scalekit account values once. You do not paste a Gmail, Slack, or GitHub token into Hermes.

- **Four tools cover the catalog.** `scalekit_list_connections`, `scalekit_authorize`, `scalekit_execute_tool`, `scalekit_proxy`.
- **One install command.** `hermes plugins install scalekit-inc/hermes-tools`.
- **The key prompt is the install.** Hermes asks for the three values and saves them to `~/.hermes/.env`.
- **A finished dashboard connection is not your approval.** The first ask for a new person returns an approval link. After you approve, the same ask returns the profile.
- **The reply has no provider token.**

## Install

These commands were run on Hermes 0.19.0. Quit any open `hermes` chat first.

```bash
hermes --version
```

Hermes 0.19.0 does not install plugin dependencies. `python -m pip` fails on that Hermes because it has no `pip` module. This command reads the Python path from the first line of the `hermes` program and installs the Scalekit package there:

```bash
uv pip install --python "$(sed -n '1s/^#!//p' "$(command -v hermes)")" 'scalekit-sdk-python>=2.12.0,<3'
```

On the test machine that Python was `~/.local/share/mise/installs/pipx-hermes-agent/0.19.0/hermes-agent/bin/python`. The package that installed was `scalekit-sdk-python` 2.21.0.

Run this step on a current Hermes too. The Scalekit package needs the `setuptools` library below version 83. Hermes pins `setuptools` 83. Those two pins cannot sit in one environment, so the plugin leaves this install to you.

```bash
hermes plugins install scalekit-inc/hermes-tools
```

`hermes plugins install scalekit` fails until the Hermes catalog lists this plugin.

If Hermes says the plugin is already installed, replace that copy:

```bash
hermes plugins install scalekit-inc/hermes-tools --force
```

Hermes then asks for three values. Paste them from [app.scalekit.com](https://app.scalekit.com), Dashboard, Developers, Settings, API Credentials. If Hermes does not ask, those values are already saved.

| Prompt | What you paste |
|---|---|
| `SCALEKIT_CLIENT_ID` | The client id. It looks like `skc_1234`. A production id can start with `prd_skc_`. |
| `SCALEKIT_CLIENT_SECRET` | The client secret. It looks like `test_abcdef1234567890`. This is the Scalekit account secret, not a Gmail or Slack token. |
| `SCALEKIT_ENVIRONMENT_URL` | The environment URL. It looks like `https://your-env.scalekit.dev`. |

When Hermes asks `Enable 'scalekit' now?`, type `Y`. The tools show up in the next `hermes` chat. Restart the gateway only if a gateway is already running.

Before you install, open AgentKit, then Connections, and write down a connection name. The test used `github-connect`. Its type was `OAUTH` and its status was `COMPLETED`. Do not copy a `conn_` id.

## Try it

```text
List my Scalekit connections.
```

```text
Who am I on GitHub? Use the connection github-connect.
```

Use your own connection name. The first time that person has not approved the app, Hermes returns an approval link and stops. Open the link. Send the same sentence again. A scheduled job cannot open that link. Approve the app in a normal chat first.

To act as another person for one turn, put that person's id in the same sentence, for example `as identifier usr_8f3a2c`.

## What the 16 Oct 2026 test showed

The account had 23 connections. All were `COMPLETED`. `github-connect` was `OAUTH`.

The first GitHub question returned an approval link. The browser page said **Successfully connected to Github.** The second question was `ACTIVE`. Hermes guessed a tool named `github_get_login`. Scalekit does not have that tool. Hermes then called `scalekit_proxy` on `/user`. The reply was the GitHub login `saif-at-scalekit`, the name, and `https://github.com/saif-at-scalekit`. It had no `refresh_token` and no `access_token`.

A later run on the same machine kept that approval. The person id was copied from `plugin-data/hermes-tools/identifier` to `plugin-data/scalekit/identifier`. The first launch on a new machine may print `Scalekit identifier created: usr_…`. You do not type it.

## Tools

| Tool | What it does |
|---|---|
| `scalekit_list_connections` | Lists the connections in your Scalekit account. |
| `scalekit_authorize` | Returns an approval link, or `ACTIVE` when this person already approved the connection. |
| `scalekit_execute_tool` | Calls one named tool after the account is `ACTIVE`. |
| `scalekit_proxy` | Calls one HTTP path when the connector has no named tool. |

The rules Hermes reads are in the bundled skill `scalekit:scalekit`. Open it before the first Scalekit action.

## Disclosure

- **Network:** the plugin's HTTP calls go to the environment URL you paste. That call lists connections, asks Scalekit for an approval link, runs a named tool, or proxies one HTTP request. You open the approval link in your browser.
- **Credentials:** install saves the three Scalekit values in the Hermes home `.env`. The plugin reads them with Hermes `get_secret`. It does not read a `.env` file itself. Provider tokens stay in Scalekit. The chat reply does not include them.
- **Stored data:** one person id at `<HERMES_HOME>/plugin-data/scalekit/identifier`. Hermes keeps that directory when you update or remove the plugin. If `plugin-data/hermes-tools/identifier` already exists, the plugin reads that file and copies the id. That read is outside this plugin's own data directory.
- **Where the tools run:** after you enable the plugin, the four tools are on every Hermes surface that shares the tool registry, including a messaging gateway. A person that gateway admits can ask Hermes to call them with your Scalekit values.
- No shell commands, no background processes, no telemetry, no self-updating. A scheduled run returns the approval link and stops.

## What this plugin does not do

- It does not create your Scalekit account.
- It does not create the connection. You create that once under AgentKit, then Connections.
- It does not install authstack. Authstack is the skill pack for Cursor, Claude Code, Copilot, and Codex.
- It does not change the skill `hermes-delegated-auth`.
- It does not register one Hermes tool per Scalekit action.
- It does not save a file returned by the proxy.

## Development

```bash
python -m pytest tests
hermes plugins validate . --install-deps
hermes plugins doctor . --ci
```

The tests use a fake Scalekit client and send no requests.

Install a local checkout with:

```bash
hermes plugins install "file://$PWD"
```
