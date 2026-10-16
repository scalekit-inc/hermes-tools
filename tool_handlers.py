"""Tool handlers. Each one returns a JSON string and does not raise."""

import importlib.util
import json
import os
from pathlib import Path


def _load_sibling(name):
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"hermes_tools_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _person_id(args, kwargs):
    identifier = (args or {}).get("identifier") or kwargs.get("identifier")
    if identifier:
        return identifier
    credentials = _load_sibling("credentials")
    root = kwargs.get("hermes_home")
    if root is None:
        root = os.environ.get("HERMES_HOME", Path.home() / ".hermes")
    identifier, _created = credentials.load_or_create_identifier(root)
    return identifier


def _client_for(kwargs):
    client = kwargs.get("client")
    if client is not None:
        return client
    return _load_sibling("adapter").build_client(kwargs.get("env"))


def _json_call(work):
    try:
        result = work()
    except Exception as exc:
        result = {"error": str(exc)}
    return json.dumps(result)


def authorize_tool(args, **kwargs):
    actions = _load_sibling("handler")
    if not (args or {}).get("connection_name"):
        return json.dumps({"error": "Name the connection, for example gmail-connect."})
    return _json_call(
        lambda: actions.authorize(
            _client_for(kwargs),
            args["connection_name"],
            _person_id(args, kwargs),
        )
    )


def execute_tool(args, **kwargs):
    actions = _load_sibling("handler")
    return _json_call(
        lambda: actions.execute(
            _client_for(kwargs),
            (args or {}).get("connection_name", ""),
            (args or {}).get("tool_name", ""),
            (args or {}).get("tool_input") or {},
            _person_id(args, kwargs),
        )
    )


def proxy_tool(args, **kwargs):
    actions = _load_sibling("handler")
    return _json_call(
        lambda: actions.proxy(
            _client_for(kwargs),
            (args or {}).get("connection_name", ""),
            _person_id(args, kwargs),
            (args or {}).get("path", ""),
            (args or {}).get("method") or "GET",
            (args or {}).get("query_params") or {},
            (args or {}).get("body"),
        )
    )


def list_connections_tool(args, **kwargs):
    del args
    actions = _load_sibling("handler")
    return _json_call(lambda: actions.list_connections(_client_for(kwargs)))


HANDLERS = {
    "scalekit_list_connections": list_connections_tool,
    "scalekit_authorize": authorize_tool,
    "scalekit_execute_tool": execute_tool,
    "scalekit_proxy": proxy_tool,
}
