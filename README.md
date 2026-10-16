# Connect Hermes Agent to 500+ connectors and 20k+ tools

Hermes can call the Scalekit catalog: 500+ connectors and 20,000+ tools, as published on [scalekit.com](https://www.scalekit.com/). Scalekit stores each person's token and refreshes it. You paste three Scalekit account values once. You do not paste a Gmail, Slack, or GitHub token into Hermes.

This page is the path that was run on Hermes 0.19.0. The same steps are what you type.

- **Four Hermes tools do the whole catalog.** `scalekit_list_connections`, `scalekit_authorize`, `scalekit_execute_tool`, `scalekit_proxy`.
- **The dashboard connection is not your approval.** `github-connect` can already be `COMPLETED`. The plugin still creates a new person id. That person must open an approval link.
- **The first GitHub question returns a link.** After you approve, the same question returns the GitHub profile.
- **A guessed tool name is refused.** Hermes tried `github_get_login`. The plugin said that tool does not exist. `scalekit_proxy` on `/user` then returned the profile.
- **The chat shows no token.** The reply has the login, the name, and the profile URL. It has no `refresh_token` and no `access_token`.

## What the chat looked like

```text
You: List my Scalekit connections.

Hermes: Your Scalekit connections (23 total). All show status COMPLETED.
        github-connect    OAUTH    COMPLETED

You: Who am I on GitHub? Use the connection github-connect.

Hermes: github-connect is not ACTIVE yet.
        Open this link to approve it.

# The browser page says: Successfully connected to Github.

You: Who am I on GitHub? Use the connection github-connect.

Hermes: Connection is ACTIVE.
        No tool named github_get_login was found.
        You're signed in on GitHub as saif-at-scalekit (via github-connect).
        Profile: https://github.com/saif-at-scalekit
```

Your connection name may differ. Your GitHub login will be the account you approved. The 23 connections were the ones on that Scalekit account during the test.

## 1. Get the code

```bash
git clone https://github.com/scalekit-inc/hermes-tools.git
cd hermes-tools
git checkout main
```

The test used this checkout:

```bash
cd /home/saif_shines/Projects/scalekit-inc/hermes-tools
git checkout main
git status -sb
```

`git status -sb` printed `## main...origin/main`.

## 2. Install the Scalekit package into Hermes

Hermes 0.19.0 does not install plugin dependencies. This command failed:

```bash
python -m pip install 'scalekit-sdk-python>=2.12.0,<3'
# /path/to/hermes/bin/python: No module named pip
```

This command worked. Point `--python` at the Python that runs `hermes`.

```bash
uv pip install --python /path/to/the/hermes/python 'scalekit-sdk-python>=2.12.0,<3'
```

The test installed `scalekit-sdk-python==2.21.0`. A current Hermes asks to install this package during plugin install. You can skip this step there.

## 3. Copy three values from the dashboard

Open [app.scalekit.com](https://app.scalekit.com).

1. Go to AgentKit, then Connections. The test used `github-connect`. Its type was `OAUTH` and its status was `COMPLETED`. Write down your connection name. Do not copy a `conn_` id.
2. Go to Developers, then Settings, then API Credentials. Leave that page open.

## 4. Install and enable the plugin

```bash
hermes plugins install file:///absolute/path/to/hermes-tools
```

Hermes prints: `Warning: Using insecure/local URL scheme.` Continue.

Hermes then asks for three values. Paste them from the API Credentials page. Each one is saved to `~/.hermes/.env`.

| Prompt | What the screen said | What we pasted |
|---|---|---|
| `SCALEKIT_CLIENT_ID` | Copy it from Dashboard, Developers, Settings, API Credentials. It looks like `skc_1234`. | The client id. A production id can start with `prd_skc_`. |
| `SCALEKIT_CLIENT_SECRET` | It looks like `test_abcdef1234567890`. This is the Scalekit account secret, not a Gmail or Slack token. | The client secret. The screen hides it. |
| `SCALEKIT_ENVIRONMENT_URL` | It looks like `https://your-env.scalekit.dev`. | The environment URL from that same page. |

Hermes then prints `Installed` and asks `Enable 'scalekit' now?` Type `Y`.

The test installed to `~/.hermes/plugins/scalekit`. Hermes also printed `hermes gateway restart`. A new `hermes` chat was enough. Restart the gateway only if a gateway is already running.

When the repository is public, `hermes plugins install scalekit-inc/hermes-tools` is the same install. After the Hermes catalog lists this plugin, the command is `hermes plugins install scalekit`. That name is an error until the listing exists.

## 5. List the connections

```bash
hermes
```

Type:

```text
List my Scalekit connections.
```

Hermes loaded the skill `scalekit:scalekit` and called `scalekit_list_connections`. The test reply started with `Your Scalekit connections (23 total). All show status COMPLETED.` and included:

```text
github-connect    OAUTH    COMPLETED
```

No token was in the list. The first launch may print `Scalekit identifier created: usr_…`. That id is the person Hermes will act as. You do not type it.

## 6. Approve the app, then ask again

In the same chat, type:

```text
Who am I on GitHub? Use the connection github-connect.
```

The test reply was:

```text
github-connect is not ACTIVE yet. Open this link to approve it.
```

Open the link. The page says **Successfully connected to Github.** Go back to the same chat and send the same sentence.

The test reply was:

```text
Connection is ACTIVE. Fetching your GitHub login.
No tool named github_get_login was found.
You're signed in on GitHub as saif-at-scalekit (via github-connect).
```

`github_get_login` is a name Hermes guessed. Scalekit does not have that tool. Hermes then called `scalekit_proxy` on `/user` and returned the profile: login, name, profile URL, company, public repo count, and followers. The reply had no `refresh_token` and no `access_token`.

Use your own connection name in the sentence. A scheduled job cannot open the approval link. Approve the app in a normal chat first.

To act as another person for one turn, put that person's id in the same sentence, for example `as identifier usr_8f3a2c`.

## What this plugin does not do

- It does not create your Scalekit account.
- It does not create the connection. You create that once under AgentKit, then Connections.
- It does not install authstack. Authstack is the skill pack for Cursor, Claude Code, Copilot, and Codex.
- It does not change the skill `hermes-delegated-auth`.
- It does not register one Hermes tool per Scalekit action. The four tools above cover the catalog.
- It does not save a file returned by the proxy.

The rules Hermes reads are in the bundled skill `scalekit:scalekit`.
