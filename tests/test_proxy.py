import importlib.util
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("hermes_tools_handler", _ROOT / "handler.py")
handler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(handler)


class FakeScalekit:
    def __init__(self, connection, account, response=None):
        self.connection = connection
        self.account = account
        self.response = response or {
            "status_code": 200,
            "content_type": "application/json",
            "body": {"ok": True},
        }
        self.proxy_calls = []
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

    def proxy_request(self, connection_name, identifier, path, method, query_params, body):
        self.proxy_calls.append(
            {
                "connection_name": connection_name,
                "identifier": identifier,
                "path": path,
                "method": method,
                "query_params": query_params,
                "body": body,
            }
        )
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _active():
    return FakeScalekit(
        connection={"key_id": "acme", "type": "OAUTH", "status": "COMPLETED"},
        account={"status": "ACTIVE"},
    )


def test_proxy_returns_json_and_strips_provider_tokens():
    client = _active()
    client.response = {
        "status_code": 200,
        "content_type": "application/json",
        "body": {"name": "Ada", "refresh_token": "secret-token"},
    }

    result = handler.proxy(client, "acme", "usr_8f3a2c", "/v1/me", "GET", {}, None)

    assert result == {"name": "Ada"}
    assert client.proxy_calls[0]["identifier"] == "usr_8f3a2c"
    assert "secret-token" not in json.dumps(result)


def test_proxy_returns_text():
    client = _active()
    client.response = {
        "status_code": 200,
        "content_type": "text/plain",
        "body": "hello",
    }

    result = handler.proxy(client, "acme", "usr_8f3a2c", "/v1/me", "GET", {}, None)

    assert result == {"text": "hello"}


def test_inactive_account_returns_a_link_and_does_not_call_the_proxy():
    client = FakeScalekit(
        connection={"key_id": "acme", "type": "OAUTH", "status": "COMPLETED"},
        account={"status": "PENDING_AUTH"},
    )

    result = handler.proxy(client, "acme", "usr_8f3a2c", "/v1/me", "GET", {}, None)

    assert result == {"authorization_link": "https://auth.example/approve"}
    assert client.proxy_calls == []


def test_error_status_returns_immediately():
    client = _active()
    client.response = {
        "status_code": 404,
        "content_type": "application/json",
        "body": {"message": "missing"},
    }

    result = handler.proxy(client, "acme", "usr_8f3a2c", "/v1/missing", "GET", {}, None)

    assert result == {"error": "Proxy request failed with status 404.", "body": {"message": "missing"}}


def test_disabled_proxy_says_the_catalog_does_not_cover_the_action():
    client = _active()
    client.response = RuntimeError("TOOL_PROXY_DISABLED")

    result = handler.proxy(client, "acme", "usr_8f3a2c", "/v1/secret", "POST", {}, {"a": 1})

    assert result == {"error": "The catalog does not cover this action."}


def test_disabled_proxy_status_body_says_the_catalog_does_not_cover_the_action():
    client = _active()
    client.response = {
        "status_code": 403,
        "content_type": "application/json",
        "body": {"code": "TOOL_PROXY_DISABLED"},
    }

    result = handler.proxy(client, "acme", "usr_8f3a2c", "/v1/secret", "GET", {}, None)

    assert result == {"error": "The catalog does not cover this action."}


def test_vendor_json_content_type_is_json_not_a_file():
    client = _active()
    client.response = {
        "status_code": 200,
        "content_type": "application/vnd.github+json",
        "body": {"login": "octocat"},
    }

    result = handler.proxy(client, "acme", "usr_8f3a2c", "/user", "GET", {}, None)

    assert result == {"login": "octocat"}
