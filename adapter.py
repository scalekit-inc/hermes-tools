"""The only module that talks to Scalekit."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _http_json(method, url, headers, body=None):
    data = None if body is None else urlencode(body).encode()
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


class ScalekitAdapter:
    """Normalize Scalekit replies into dicts the handler can read."""

    def __init__(self, env):
        self._env = env
        self._sdk = None

    def _client(self):
        if self._sdk is None:
            import scalekit.client as scalekit_sdk

            self._sdk = scalekit_sdk.ScalekitClient(
                self._env["SCALEKIT_ENVIRONMENT_URL"],
                self._env["SCALEKIT_CLIENT_ID"],
                self._env["SCALEKIT_CLIENT_SECRET"],
            )
        return self._sdk

    def _token(self):
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
        return payload["access_token"]

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
        account = self._client().connect.get_or_create_connected_account(
            connection_name=connection_name,
            identifier=identifier,
        ).connected_account
        return {"status": account.status}

    def get_connected_account(self, connection_name, identifier):
        try:
            account = self._client().actions.get_connected_account(
                connection_name=connection_name,
                identifier=identifier,
            ).connected_account
        except (HTTPError, URLError, OSError, RuntimeError):
            return None
        return {"status": account.status}

    def get_authorization_link(self, connection_name, identifier):
        link = self._client().connect.get_authorization_link(
            connection_name=connection_name,
            identifier=identifier,
        )
        return link.link


def build_client(env=None):
    return ScalekitAdapter(os.environ if env is None else env)
