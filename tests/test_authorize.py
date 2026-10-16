import importlib.util
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, _ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


handler = _load("hermes_tools_handler", "handler.py")
plugin = _load("hermes_tools_plugin", "__init__.py")


class FakeScalekit:
    def __init__(self, connection=None, account=None, link="https://auth.example/approve"):
        self.connection = connection
        self.account = account or {"status": "PENDING_AUTH"}
        self.link = link
        self.link_calls = 0
        self.execute_calls = 0

    def find_connection(self, name):
        del name
        return self.connection

    def get_or_create_connected_account(self, connection_name, identifier):
        del connection_name, identifier
        return self.account

    def get_connected_account(self, connection_name, identifier):
        del connection_name, identifier
        return self.account

    def get_authorization_link(self, connection_name, identifier):
        del connection_name, identifier
        self.link_calls += 1
        return self.link

    def execute_tool(self, **kwargs):
        del kwargs
        self.execute_calls += 1
        return {"should": "not run"}


def test_missing_connection_tells_the_standing_assistant_to_create_it():
    result = handler.authorize(FakeScalekit(connection=None), "gmail-connect", "usr_8f3a2c")

    assert result == {
        "error": "Create the gmail-connect connection in the Scalekit dashboard under AgentKit, Connections."
    }


def test_inactive_oauth_account_returns_an_authorization_link_and_does_not_run_a_tool():
    client = FakeScalekit(
        connection={"key_id": "gmail-connect", "type": "OAUTH", "status": "COMPLETED"},
        account={"status": "PENDING_AUTH"},
    )

    result = handler.authorize(client, "gmail-connect", "usr_8f3a2c")

    assert result == {"authorization_link": "https://auth.example/approve"}
    assert client.link_calls == 1
    assert client.execute_calls == 0


def test_draft_connection_tells_the_standing_assistant_to_finish_it():
    client = FakeScalekit(
        connection={"key_id": "gmail-connect", "type": "OAUTH", "status": "DRAFT"},
    )

    result = handler.authorize(client, "gmail-connect", "usr_8f3a2c")

    assert result == {"error": "Finish the gmail-connect connection in the Scalekit dashboard."}
    assert client.link_calls == 0


def test_active_account_reports_active_and_does_not_ask_for_a_link():
    client = FakeScalekit(
        connection={"key_id": "gmail-connect", "type": "OAUTH", "status": "COMPLETED"},
        account={"status": "ACTIVE"},
    )

    result = handler.authorize(client, "gmail-connect", "usr_8f3a2c")

    assert result == {"status": "ACTIVE"}
    assert client.link_calls == 0


def test_register_publishes_the_authorize_tool_and_the_skill(tmp_path):
    class Ctx:
        def __init__(self):
            self.tools = []
            self.skills = []

        def register_tool(self, name, toolset, schema, tool_handler, **kwargs):
            self.tools.append((name, schema, tool_handler))

        def register_skill(self, name, path, description=""):
            self.skills.append((name, Path(path), description))

    env = {
        "SCALEKIT_CLIENT_ID": "skc_test",
        "SCALEKIT_CLIENT_SECRET": "secret",
        "SCALEKIT_ENVIRONMENT_URL": "https://example.scalekit.dev",
    }
    ctx = Ctx()
    plugin.register(ctx, env=env, hermes_home=tmp_path)

    authorize = next(tool for tool in ctx.tools if tool[0] == "scalekit_authorize")
    assert "scalekit:scalekit" in authorize[1]["description"]
    skill_name, skill_path, _description = ctx.skills[0]
    assert skill_name == "scalekit"
    assert skill_path.read_text().count("Provider tokens stay in Scalekit") == 1
    body = json.loads(authorize[2](
        {"connection_name": "gmail-connect"},
        client=FakeScalekit(connection=None),
        identifier="usr_8f3a2c",
        env=env,
    ))
    assert "Create the gmail-connect connection" in body["error"]
