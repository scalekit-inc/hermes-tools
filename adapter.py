"""The only module that talks to Scalekit."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _http_json(method, url, headers, body=None):
    data = None if body is None else urlencode(body).encode()
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def _decode(content_type, raw):
    if "json" in content_type.lower():
        try:
            return json.loads(raw.decode())
        except ValueError:
            return raw.decode(errors="replace")
    if content_type.startswith("text/"):
        return raw.decode(errors="replace")
    return None


class ScalekitAdapter:
    """Normalize Scalekit replies into dicts the handler can read."""

    def __init__(self, env):
        self._env = env
        self._access_token = None

    def _token(self):
        if self._access_token is None:
            base = self._env["SCALEKIT_ENVIRONMENT_URL"].rstrip("/")
            payload = _http_json(
                "POST",
                f"{base}/oauth/token",
                {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
                {
                    "grant_type": "client_credentials",
                    "client_id": self._env["SCALEKIT_CLIENT_ID"],
                    "client_secret": self._env["SCALEKIT_CLIENT_SECRET"],
                },
            )
            self._access_token = payload["access_token"]
        return self._access_token

    def _api(self, method, path, query=None, body=None):
        base = self._env["SCALEKIT_ENVIRONMENT_URL"].rstrip("/")
        url = f"{base}{path}" + (f"?{urlencode(query)}" if query else "")
        headers = {"Authorization": f"Bearer {self._token()}", "Accept": "application/json"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            message = _decode(exc.headers.get("Content-Type", "") if exc.headers else "", exc.read())
            if isinstance(message, dict):
                message = message.get("message")
            raise HTTPError(url, exc.code, message or exc.reason, exc.headers, None) from None

    def find_connection(self, name):
        base = self._env["SCALEKIT_ENVIRONMENT_URL"].rstrip("/")
        headers = {"Authorization": f"Bearer {self._token()}", "Accept": "application/json"}
        page_token = ""
        while True:
            query = urlencode({"page_size": 30, "page_token": page_token})
            data = _http_json("GET", f"{base}/api/v1/connections/app?{query}", headers)
            for connection in data.get("connections", []):
                if connection.get("key_id") == name:
                    return connection
            page_token = data.get("next_page_token") or ""
            if not page_token:
                return None

    def get_or_create_connected_account(self, connection_name, identifier):
        account = self.get_connected_account(connection_name, identifier)
        if account is not None:
            return account
        created = self._api(
            "POST",
            "/api/v1/connected_accounts",
            body={"connector": connection_name, "identifier": identifier, "connected_account": {}},
        )
        return {"status": created["connected_account"]["status"]}

    def get_connected_account(self, connection_name, identifier):
        try:
            data = self._api(
                "GET",
                "/api/v1/connected_accounts/auth",
                {"connector": connection_name, "identifier": identifier},
            )
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise
        return {"status": data["connected_account"]["status"]}

    def get_authorization_link(self, connection_name, identifier):
        data = self._api(
            "POST",
            "/api/v1/connected_accounts/magic_link",
            body={"connector": connection_name, "identifier": identifier},
        )
        return data["link"]

    def get_tool_schema(self, tool_name):
        data = self._api("GET", "/api/v1/tools", {"filter.tool_name": tool_name})
        tools = data.get("tools") or []
        if not tools:
            return None
        return tools[0]

    def execute_tool(self, tool_name, connection_name, identifier, tool_input):
        return self._api(
            "POST",
            "/api/v1/execute_tool",
            body={
                "tool_name": tool_name,
                "connector": connection_name,
                "identifier": identifier,
                "params": tool_input or {},
            },
        )

    def proxy_request(self, connection_name, identifier, path, method, query_params, body):
        base = self._env["SCALEKIT_ENVIRONMENT_URL"].rstrip("/")
        url = f"{base}/proxy{path}" + (f"?{urlencode(query_params)}" if query_params else "")
        headers = {
            "Authorization": f"Bearer {self._token()}",
            "connection_name": connection_name,
            "identifier": identifier,
        }
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        request = Request(url, data=data, headers=headers, method=(method or "GET").upper())
        try:
            with urlopen(request, timeout=30) as response:
                status, response_headers, raw = response.status, response.headers, response.read()
        except HTTPError as exc:
            status, response_headers, raw = exc.code, exc.headers or {}, exc.read()
        content_type = response_headers.get("Content-Type", "") or ""
        return {"status_code": status, "content_type": content_type, "body": _decode(content_type, raw)}

    def list_connections(self):
        base = self._env["SCALEKIT_ENVIRONMENT_URL"].rstrip("/")
        headers = {"Authorization": f"Bearer {self._token()}", "Accept": "application/json"}
        page_token = ""
        found = []
        while True:
            query = urlencode({"page_size": 30, "page_token": page_token})
            data = _http_json("GET", f"{base}/api/v1/connections/app?{query}", headers)
            found.extend(data.get("connections", []))
            page_token = data.get("next_page_token") or ""
            if not page_token:
                return found


def build_client(env):
    return ScalekitAdapter(env)
