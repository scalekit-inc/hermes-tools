"""What Hermes reads to decide when to call Scalekit."""

AUTHORIZE = {
    "name": "scalekit_authorize",
    "description": (
        "Approve one Scalekit connection for the standing assistant. "
        "Open skill scalekit:scalekit before the first Scalekit action. "
        "Use the connection name from AgentKit, Connections, not a conn_ id. "
        "If the account is not ACTIVE, return the authorization link and do not run a tool. "
        "Provider tokens stay in Scalekit. A scheduled run cannot open the link."
    ),
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
}

EXECUTE = {
    "name": "scalekit_execute_tool",
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
                "description": "Scalekit tool name returned by that connector's schema.",
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
}

PROXY = {
    "name": "scalekit_proxy",
    "description": (
        "Call a connector API through Scalekit when no named tool exists. "
        "Open skill scalekit:scalekit before the first Scalekit action. "
        "If the account is not ACTIVE, return the authorization link and do not call the proxy. "
        "An unsupported action returns an error and does not wait. "
        "Provider tokens stay in Scalekit."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "connection_name": {
                "type": "string",
                "description": "Connection name from AgentKit, Connections.",
            },
            "path": {"type": "string", "description": "API path, for example /user."},
            "method": {"type": "string", "description": "HTTP method. Defaults to GET."},
            "query_params": {"type": "object", "description": "Query string parameters."},
            "body": {"type": "object", "description": "JSON request body."},
            "identifier": {
                "type": "string",
                "description": "Person id for this call. Omit to use the stored identifier.",
            },
        },
        "required": ["connection_name", "path"],
    },
}

LIST_CONNECTIONS = {
    "name": "scalekit_list_connections",
    "description": (
        "List Scalekit connections on this account. "
        "Each row has the connection name, type, and status. "
        "Provider tokens are not included."
    ),
    "parameters": {"type": "object", "properties": {}},
}

TOOLS = (LIST_CONNECTIONS, AUTHORIZE, EXECUTE, PROXY)
