import importlib.util
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("hermes_tools_handler", _ROOT / "handler.py")
handler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(handler)


class FakeScalekit:
    def __init__(self, connection, account, schema=None, result=None):
        self.connection = connection
        self.account = account
        self.schema = schema
        self.result = result or {"login": "octocat"}
        self.execute_calls = []
        self.link_calls = 0

    def find_connection(self, name):
        del name
        return self.connection

    def get_or_create_connected_account(self, connection_name, identifier):
        del connection_name, identifier
        return self.account

    def get_authorization_link(self, connection_name, identifier):
        del connection_name, identifier
        self.link_calls += 1
        return "https://auth.example/approve"

    def get_tool_schema(self, tool_name):
        del tool_name
        return self.schema

    def execute_tool(self, tool_name, connection_name, identifier, tool_input):
        self.execute_calls.append(
            {
                "tool_name": tool_name,
                "connection_name": connection_name,
                "identifier": identifier,
                "tool_input": tool_input,
            }
        )
        return self.result

    def list_connections(self):
        return [
            {"key_id": "gmail-connect", "type": "OAUTH", "status": "COMPLETED", "access_token": "hidden"},
        ]


def _active_client(**kwargs):
    return FakeScalekit(
        connection={"key_id": "github-connect", "type": "OAUTH", "status": "COMPLETED"},
        account={"status": "ACTIVE", "id": "ca_1"},
        schema={"name": "github_get_login"},
        **kwargs,
    )


def test_active_account_returns_the_tool_result_without_provider_tokens():
    client = _active_client(result={"login": "octocat", "refresh_token": "secret-token"})

    result = handler.execute(client, "github-connect", "github_get_login", {}, "usr_8f3a2c")

    assert result["login"] == "octocat"
    assert "refresh_token" not in result
    assert "secret-token" not in json.dumps(result)


def test_identifier_on_the_call_is_the_id_sent_to_scalekit():
    client = _active_client()

    handler.execute(client, "github-connect", "github_get_login", {"a": 1}, "usr_other")

    assert client.execute_calls[0]["identifier"] == "usr_other"


def test_inactive_account_returns_a_link_and_does_not_run_the_tool():
    client = FakeScalekit(
        connection={"key_id": "github-connect", "type": "OAUTH", "status": "COMPLETED"},
        account={"status": "PENDING_AUTH"},
        schema={"name": "github_get_login"},
    )

    result = handler.execute(client, "github-connect", "github_get_login", {}, "usr_8f3a2c")

    assert result == {"authorization_link": "https://auth.example/approve"}
    assert client.execute_calls == []


def test_scalekit_error_becomes_json():
    client = _active_client()

    def explode(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("tool execution failed")

    client.execute_tool = explode

    result = handler.execute(client, "github-connect", "github_get_login", {}, "usr_8f3a2c")

    assert result == {"error": "tool execution failed"}


def test_list_connections_returns_names_without_tokens():
    result = handler.list_connections(FakeScalekit(connection=None, account=None))

    assert result == {
        "connections": [
            {"connection_name": "gmail-connect", "type": "OAUTH", "status": "COMPLETED"},
        ]
    }
