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
