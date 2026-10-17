"""The adapter speaks Scalekit's REST API. These tests pin each request."""

import importlib.util
import io
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("hermes_tools_adapter", _ROOT / "adapter.py")
adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter)

BASE = "https://example.scalekit.dev"
ENV = {
    "SCALEKIT_ENVIRONMENT_URL": BASE + "/",
    "SCALEKIT_CLIENT_ID": "skc_test",
    "SCALEKIT_CLIENT_SECRET": "test_secret",
}


class _Response:
    def __init__(self, status, body, content_type="application/json"):
        self.status = status
        self.headers = {"Content-Type": content_type}
        self._body = body if isinstance(body, bytes) else json.dumps(body).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeScalekitServer:
    """Answer requests by (method, path). Record every request after the token."""

    def __init__(self, routes):
        self.routes = routes
        self.requests = []
        self.token_calls = 0

    def __call__(self, request, timeout=None):
        url = urlsplit(request.full_url)
        if url.path == "/oauth/token":
            self.token_calls += 1
            return _Response(200, {"access_token": "sk_access"})
        body = json.loads(request.data) if request.data else None
        self.requests.append(
            {
                "method": request.get_method(),
                "path": url.path,
                "query": parse_qs(url.query),
                "headers": {k.lower(): v for k, v in request.header_items()},
                "body": body,
            }
        )
        status, payload, *rest = self.routes[(request.get_method(), url.path)]
        if status >= 400:
            raise HTTPError(request.full_url, status, "error", {"Content-Type": "application/json"}, io.BytesIO(json.dumps(payload).encode()))
        return _Response(status, payload, *rest)


@pytest.fixture
def server(monkeypatch):
    def install(routes):
        fake = FakeScalekitServer(routes)
        monkeypatch.setattr(adapter, "urlopen", fake)
        return fake

    return install


def test_existing_account_is_returned_without_a_create(server):
    fake = server({("GET", "/api/v1/connected_accounts/auth"): (200, {"connected_account": {"status": "ACTIVE", "id": "ca_1"}})})
    account = adapter.build_client(ENV).get_or_create_connected_account("github-connect", "usr_1")
    assert account == {"status": "ACTIVE"}
    assert [r["method"] for r in fake.requests] == ["GET"]
    assert fake.requests[0]["query"] == {"connector": ["github-connect"], "identifier": ["usr_1"]}
    assert fake.requests[0]["headers"]["authorization"] == "Bearer sk_access"


def test_missing_account_is_created(server):
    fake = server(
        {
            ("GET", "/api/v1/connected_accounts/auth"): (404, {"message": "not found"}),
            ("POST", "/api/v1/connected_accounts"): (200, {"connected_account": {"status": "PENDING_AUTH"}}),
        }
    )
    account = adapter.build_client(ENV).get_or_create_connected_account("github-connect", "usr_1")
    assert account == {"status": "PENDING_AUTH"}
    assert fake.requests[1]["body"] == {
        "connector": "github-connect",
        "identifier": "usr_1",
        "connected_account": {},
    }
    assert fake.token_calls == 1


def test_get_connected_account_returns_none_when_missing(server):
    server({("GET", "/api/v1/connected_accounts/auth"): (404, {})})
    assert adapter.build_client(ENV).get_connected_account("jira", "usr_1") is None


def test_authorization_link_comes_from_the_magic_link_endpoint(server):
    fake = server({("POST", "/api/v1/connected_accounts/magic_link"): (200, {"link": "https://auth.example/approve"})})
    link = adapter.build_client(ENV).get_authorization_link("github-connect", "usr_1")
    assert link == "https://auth.example/approve"
    assert fake.requests[0]["body"] == {"connector": "github-connect", "identifier": "usr_1"}


def test_tool_schema_is_filtered_by_name(server):
    fake = server({("GET", "/api/v1/tools"): (200, {"tools": [{"definition": {"name": "github_user_get"}}]})})
    schema = adapter.build_client(ENV).get_tool_schema("github_user_get")
    assert schema == {"definition": {"name": "github_user_get"}}
    assert fake.requests[0]["query"] == {"filter.tool_name": ["github_user_get"]}


def test_unknown_tool_schema_is_none(server):
    server({("GET", "/api/v1/tools"): (200, {"tools": []})})
    assert adapter.build_client(ENV).get_tool_schema("nope") is None


def test_execute_tool_posts_the_input_for_the_person(server):
    fake = server({("POST", "/api/v1/execute_tool"): (200, {"data": {"login": "octo"}, "execution_id": "ex_1"})})
    result = adapter.build_client(ENV).execute_tool("github_user_get", "github-connect", "usr_1", {"a": 1})
    assert result == {"data": {"login": "octo"}, "execution_id": "ex_1"}
    assert fake.requests[0]["body"] == {
        "tool_name": "github_user_get",
        "connector": "github-connect",
        "identifier": "usr_1",
        "params": {"a": 1},
    }


def test_scalekit_error_message_reaches_the_caller(server):
    server({("POST", "/api/v1/execute_tool"): (400, {"code": 3, "message": "missing value for \"input.owner\""})})
    with pytest.raises(HTTPError) as caught:
        adapter.build_client(ENV).execute_tool("github_pull_request_get", "github-connect", "usr_1", {})
    assert caught.value.code == 400
    assert 'missing value for "input.owner"' in str(caught.value)


def test_proxy_sends_the_path_and_names_the_connection(server):
    fake = server({("POST", "/proxy/user/repos"): (201, {"id": 7})})
    result = adapter.build_client(ENV).proxy_request(
        "github-connect", "usr_1", "/user/repos", "post", {"per_page": "5"}, {"name": "demo"}
    )
    assert result == {"status_code": 201, "content_type": "application/json", "body": {"id": 7}}
    sent = fake.requests[0]
    assert sent["query"] == {"per_page": ["5"]}
    assert sent["body"] == {"name": "demo"}
    assert sent["headers"]["connection_name"] == "github-connect"
    assert sent["headers"]["identifier"] == "usr_1"


def test_proxy_returns_provider_errors_instead_of_raising(server):
    server({("GET", "/proxy/missing"): (404, {"message": "Not Found"})})
    result = adapter.build_client(ENV).proxy_request("github-connect", "usr_1", "/missing", "GET", {}, None)
    assert result["status_code"] == 404
    assert result["body"] == {"message": "Not Found"}


def test_proxy_returns_text_bodies_as_text(server):
    server({("GET", "/proxy/readme"): (200, b"hello", "text/plain")})
    result = adapter.build_client(ENV).proxy_request("github-connect", "usr_1", "/readme", "GET", {}, None)
    assert result == {"status_code": 200, "content_type": "text/plain", "body": "hello"}


def test_list_connections_still_pages(server):
    pages = iter(
        [
            (200, {"connections": [{"key_id": "a"}], "next_page_token": "p2"}),
            (200, {"connections": [{"key_id": "b"}], "next_page_token": ""}),
        ]
    )
    fake = server({})
    fake.routes = type("Pages", (), {"__getitem__": lambda self, key: next(pages)})()
    assert [c["key_id"] for c in adapter.build_client(ENV).list_connections()] == ["a", "b"]
    assert fake.requests[1]["query"]["page_token"] == ["p2"]
