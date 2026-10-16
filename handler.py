"""Decide what Hermes shows when a standing assistant names a connector."""


def authorize(client, connection_name, identifier):
    """Return an approval link, an active status, or a dashboard instruction.

    The client is a Scalekit adapter or a test double. This function does not
    import the Scalekit SDK and does not run a tool.
    """
    connection = client.find_connection(connection_name)
    if connection is None:
        return {
            "error": (
                f"Create the {connection_name} connection in the Scalekit "
                "dashboard under AgentKit, Connections."
            )
        }
    if connection.get("status") != "COMPLETED":
        return {
            "error": f"Finish the {connection_name} connection in the Scalekit dashboard."
        }

    if connection.get("type", "OAUTH").upper() == "OAUTH":
        account = client.get_or_create_connected_account(connection_name, identifier)
        if account.get("status") == "ACTIVE":
            return {"status": "ACTIVE"}
        return {"authorization_link": client.get_authorization_link(connection_name, identifier)}

    account = client.get_connected_account(connection_name, identifier)
    if account is None or account.get("status") != "ACTIVE":
        return {
            "error": f"Finish the {connection_name} connection in the Scalekit dashboard."
        }
    return {"status": "ACTIVE"}


_TOKEN_KEYS = {"access_token", "refresh_token", "id_token", "client_secret", "token"}


def _without_tokens(value):
    if isinstance(value, dict):
        return {
            key: _without_tokens(item)
            for key, item in value.items()
            if key not in _TOKEN_KEYS
        }
    if isinstance(value, list):
        return [_without_tokens(item) for item in value]
    return value


def execute(client, connection_name, tool_name, tool_input, identifier):
    """Return a tool result, an approval link, or an error. Never a provider token."""
    gate = authorize(client, connection_name, identifier)
    if gate.get("status") != "ACTIVE":
        return gate
    if not client.get_tool_schema(tool_name):
        return {"error": f"No tool named {tool_name} was found."}
    try:
        raw = client.execute_tool(tool_name, connection_name, identifier, tool_input or {})
    except Exception as exc:
        return {"error": str(exc)}
    if not isinstance(raw, dict):
        raw = {"result": raw}
    return _without_tokens(raw)


def proxy(client, connection_name, identifier, path, method, query_params, body):
    """Return a proxy result, an approval link, or an error. Do not wait."""
    gate = authorize(client, connection_name, identifier)
    if gate.get("status") != "ACTIVE":
        return gate
    try:
        raw = client.proxy_request(
            connection_name=connection_name,
            identifier=identifier,
            path=path,
            method=method or "GET",
            query_params=query_params or {},
            body=body,
        )
    except Exception as exc:
        if "TOOL_PROXY_DISABLED" in str(exc):
            return {"error": "The catalog does not cover this action."}
        return {"error": str(exc)}
    status = raw.get("status_code", 200)
    payload = raw.get("body")
    if status >= 400:
        return {
            "error": f"Proxy request failed with status {status}.",
            "body": _without_tokens(payload),
        }
    content_type = raw.get("content_type") or ""
    if isinstance(payload, (dict, list)) or "application/json" in content_type:
        return _without_tokens(payload)
    if isinstance(payload, str) or content_type.startswith("text/"):
        return {"text": payload}
    return {"error": "This response is a file. Saving files is not available yet."}


def list_connections(client):
    """Return connection names only. Leave tokens out."""
    return {
        "connections": [
            {
                "connection_name": connection.get("key_id"),
                "type": connection.get("type"),
                "status": connection.get("status"),
            }
            for connection in client.list_connections()
        ]
    }
