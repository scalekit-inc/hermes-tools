"""Hermes plugin: the tools layer for any Scalekit connector."""

import importlib.util
import json
import os
import secrets
from pathlib import Path

REQUIRED_CREDENTIALS = (
    "SCALEKIT_CLIENT_ID",
    "SCALEKIT_CLIENT_SECRET",
    "SCALEKIT_ENVIRONMENT_URL",
)


def missing_credential_message(env):
    """Name each Scalekit value that is empty. Return None when all are set."""
    missing = [name for name in REQUIRED_CREDENTIALS if not env.get(name)]
    if not missing:
        return None
    return "Missing Scalekit credentials: " + ", ".join(missing)


def _identifier_file(hermes_home):
    return Path(hermes_home) / "plugin-data" / "hermes-tools" / "identifier"


def load_or_create_identifier(hermes_home):
    """Return the stored identifier. Create usr_<hex> on the first call."""
    path = _identifier_file(hermes_home)
    if path.exists():
        current = path.read_text().strip()
        if current:
            return current, False
    created = "usr_" + secrets.token_hex(4)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(created + "\n")
    return created, True


def _load_sibling(name):
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"hermes_tools_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUTHORIZE_DESCRIPTION = (
    "Approve one Scalekit connection for the standing assistant. "
    "Open skill scalekit:scalekit before the first Scalekit action. "
    "Use the connection name from AgentKit, Connections, not a conn_ id. "
    "If the account is not ACTIVE, return the authorization link and do not run a tool. "
    "Provider tokens stay in Scalekit. A scheduled run cannot open the link."
)


def _authorize_tool(args, **kwargs):
    actions = _load_sibling("handler")
    client = kwargs.get("client")
    if client is None:
        client = _load_sibling("adapter").build_client(kwargs.get("env"))
    identifier = args.get("identifier") or kwargs.get("identifier")
    if not identifier:
        root = kwargs.get("hermes_home")
        if root is None:
            root = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
        identifier, _created = load_or_create_identifier(root)
    if not args.get("connection_name"):
        return json.dumps({"error": "Name the connection, for example gmail-connect."})
    try:
        result = actions.authorize(client, args["connection_name"], identifier)
    except Exception as exc:
        result = {"error": str(exc)}
    return json.dumps(result)


def register(ctx, env=None, hermes_home=None):
    """Load the plugin. Stop, and name the missing value, before any Scalekit call."""
    source = os.environ if env is None else env
    message = missing_credential_message(source)
    if message:
        raise RuntimeError(message)
    root = Path(hermes_home) if hermes_home is not None else Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    identifier, created = load_or_create_identifier(root)
    if created:
        print(f"Scalekit identifier created: {identifier}", flush=True)
    if hasattr(ctx, "register_tool"):
        ctx.register_tool(
            "scalekit_authorize",
            "scalekit",
            {
                "description": AUTHORIZE_DESCRIPTION,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Connection name from AgentKit, Connections. Example: gmail-connect.",
                        },
                        "identifier": {
                            "type": "string",
                            "description": "Person id for this call. Omit to use the stored identifier.",
                        },
                    },
                    "required": ["connection_name"],
                },
            },
            _authorize_tool,
        )
        ctx.register_tool(
            "scalekit_execute_tool",
            "scalekit",
            {
                "description": (
                    "Call one Scalekit tool after the connected account is ACTIVE. "
                    "Open skill scalekit:scalekit before the first Scalekit action. "
                    "If the account is not ACTIVE, return the authorization link and do not run the tool. "
                    "Omit identifier to use the stored person id. "
                    "Provider tokens stay in Scalekit."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "connection_name": {
                            "type": "string",
                            "description": "Connection name from AgentKit, Connections. Example: github-connect.",
                        },
                        "tool_name": {
                            "type": "string",
                            "description": "Scalekit tool name, for example github_get_login.",
                        },
                        "tool_input": {
                            "type": "object",
                            "description": "Arguments from that tool's schema.",
                        },
                        "identifier": {
                            "type": "string",
                            "description": "Person id for this call. Omit to use the stored identifier.",
                        },
                    },
                    "required": ["connection_name", "tool_name"],
                },
            },
            _execute_tool,
        )
        ctx.register_tool(
            "scalekit_list_connections",
            "scalekit",
            {
                "description": (
                    "List Scalekit connections on this account. "
                    "Each row has the connection name, type, and status. "
                    "Provider tokens are not included."
                ),
                "parameters": {"type": "object", "properties": {}},
            },
            _list_connections_tool,
        )
        ctx.register_skill(
            "scalekit",
            Path(__file__).resolve().parent / "skills" / "scalekit" / "SKILL.md",
            "Rules for acting in an app through Scalekit.",
        )
    return identifier


def _person_id(args, kwargs):
    identifier = args.get("identifier") or kwargs.get("identifier")
    if identifier:
        return identifier
    root = kwargs.get("hermes_home")
    if root is None:
        root = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    identifier, _created = load_or_create_identifier(root)
    return identifier


def _client_for(kwargs):
    client = kwargs.get("client")
    if client is not None:
        return client
    return _load_sibling("adapter").build_client(kwargs.get("env"))


def _execute_tool(args, **kwargs):
    actions = _load_sibling("handler")
    try:
        result = actions.execute(
            _client_for(kwargs),
            args.get("connection_name", ""),
            args.get("tool_name", ""),
            args.get("tool_input") or {},
            _person_id(args, kwargs),
        )
    except Exception as exc:
        result = {"error": str(exc)}
    return json.dumps(result)


def _list_connections_tool(args, **kwargs):
    del args
    actions = _load_sibling("handler")
    try:
        result = actions.list_connections(_client_for(kwargs))
    except Exception as exc:
        result = {"error": str(exc)}
    return json.dumps(result)
