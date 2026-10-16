import importlib.util
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("hermes_tools_plugin", _ROOT / "__init__.py")
plugin = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(plugin)

REQUIRED_CREDENTIALS = plugin.REQUIRED_CREDENTIALS
missing_credential_message = plugin.missing_credential_message
register = plugin.register


def _values():
    return {
        "SCALEKIT_CLIENT_ID": "skc_test",
        "SCALEKIT_CLIENT_SECRET": "secret",
        "SCALEKIT_ENVIRONMENT_URL": "https://example.scalekit.dev",
    }


def test_plugin_stops_and_names_each_missing_credential():
    message = missing_credential_message({})

    assert message is not None
    for name in REQUIRED_CREDENTIALS:
        assert name in message
    assert "SCALEKIT_IDENTIFIER" not in message


def test_plugin_names_only_the_credential_that_is_missing():
    present = _values()
    present["SCALEKIT_CLIENT_SECRET"] = ""

    message = missing_credential_message(present)

    assert message is not None
    assert "SCALEKIT_CLIENT_SECRET" in message
    assert "SCALEKIT_CLIENT_ID" not in message


def test_install_asks_for_the_three_scalekit_values_with_guidance():
    manifest = (_ROOT / "plugin.yaml").read_text()

    for name in REQUIRED_CREDENTIALS:
        assert f"name: {name}" in manifest
    assert "SCALEKIT_IDENTIFIER" not in manifest
    assert manifest.count("Copy it from Dashboard, Developers, Settings, API Credentials") == 3
    assert "skc_1234" in manifest
    assert "test_" in manifest
    assert "https://your-env.scalekit.dev" in manifest
    assert "python_runtime" not in manifest


def test_register_creates_an_identifier_and_keeps_it(tmp_path, capsys):
    first = register(ctx=object(), env=_values(), hermes_home=tmp_path)
    second = register(ctx=object(), env=_values(), hermes_home=tmp_path)
    shown = capsys.readouterr().out
    stored = tmp_path / "plugin-data" / "scalekit" / "identifier"

    assert first.startswith("usr_")
    assert second == first
    assert stored.read_text().strip() == first
    assert not (tmp_path / "plugin-data" / "hermes-tools" / "identifier").exists()
    assert first in shown
    assert shown.count(first) == 1


class _Ctx:
    def __init__(self):
        self.tools = {}

    def register_tool(self, name, toolset, schema, tool_handler, **kwargs):
        del toolset, schema, kwargs
        self.tools[name] = tool_handler

    def register_skill(self, name, path, description=""):
        del name, path, description


def test_hermes_discovery_does_not_read_secrets(tmp_path, monkeypatch, capsys):
    import types

    def boom(name, default=None):
        del name, default
        raise RuntimeError("unscoped")

    secret_scope = types.ModuleType("agent.secret_scope")
    secret_scope.get_secret = boom
    monkeypatch.setitem(sys.modules, "agent", types.ModuleType("agent"))
    monkeypatch.setitem(sys.modules, "agent.secret_scope", secret_scope)
    ctx = _Ctx()

    result = register(ctx, hermes_home=tmp_path)

    assert result is None
    assert set(ctx.tools) == {
        "scalekit_authorize",
        "scalekit_execute_tool",
        "scalekit_list_connections",
        "scalekit_proxy",
    }
    assert list(tmp_path.rglob("identifier")) == []
    assert capsys.readouterr().out == ""
    body = json.loads(ctx.tools["scalekit_list_connections"]({}))
    assert body["error"] == "unscoped"


def test_register_publishes_tools_when_credentials_are_missing(tmp_path):
    ctx = _Ctx()

    result = register(ctx, env={}, hermes_home=tmp_path)

    assert result is None
    assert set(ctx.tools) == {
        "scalekit_authorize",
        "scalekit_execute_tool",
        "scalekit_list_connections",
        "scalekit_proxy",
    }
    for handler in ctx.tools.values():
        body = json.loads(handler({}, env={}))
        assert "SCALEKIT_CLIENT_ID" in body["error"]
        assert "SCALEKIT_CLIENT_SECRET" in body["error"]
        assert "SCALEKIT_ENVIRONMENT_URL" in body["error"]
    assert list(tmp_path.rglob("identifier")) == []


def test_register_keeps_an_identifier_saved_under_the_old_folder(tmp_path, capsys):
    old = tmp_path / "plugin-data" / "hermes-tools" / "identifier"
    old.parent.mkdir(parents=True)
    old.write_text("usr_kept\n")

    found = register(ctx=object(), env=_values(), hermes_home=tmp_path)

    assert found == "usr_kept"
    assert (tmp_path / "plugin-data" / "scalekit" / "identifier").read_text().strip() == "usr_kept"
    assert "Scalekit identifier created" not in capsys.readouterr().out


def test_secret_reader_wins_over_the_process_environment(monkeypatch):
    monkeypatch.setenv("SCALEKIT_CLIENT_ID", "from-env")

    def reader(name, default=None):
        return {
            "SCALEKIT_CLIENT_ID": "from-secret",
            "SCALEKIT_CLIENT_SECRET": "secret",
            "SCALEKIT_ENVIRONMENT_URL": "https://example.scalekit.dev",
        }.get(name, default)

    values = plugin.read_credentials(secret_reader=reader)

    assert values["SCALEKIT_CLIENT_ID"] == "from-secret"


def test_missing_secret_api_does_not_read_the_process_environment(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "agent" or name.startswith("agent."):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "agent.secret_scope", raising=False)
    monkeypatch.setattr(builtins, "__import__", blocked)
    monkeypatch.setenv("SCALEKIT_CLIENT_ID", "from-env")
    monkeypatch.setenv("SCALEKIT_CLIENT_SECRET", "from-env")
    monkeypatch.setenv("SCALEKIT_ENVIRONMENT_URL", "https://from-env.example")

    values = plugin.read_credentials()

    assert values == {name: "" for name in REQUIRED_CREDENTIALS}


def test_register_copies_the_old_identifier_when_plugin_data_dir_is_used(tmp_path, monkeypatch, capsys):
    import types

    old = tmp_path / "plugin-data" / "hermes-tools" / "identifier"
    old.parent.mkdir(parents=True)
    old.write_text("usr_kept\n")
    storage = types.ModuleType("plugins.plugin_storage")

    def plugin_data_dir(name):
        path = tmp_path / "plugin-data" / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    storage.plugin_data_dir = plugin_data_dir
    monkeypatch.setitem(sys.modules, "plugins", types.ModuleType("plugins"))
    monkeypatch.setitem(sys.modules, "plugins.plugin_storage", storage)

    found = register(ctx=object(), env=_values(), hermes_home=None)

    assert found == "usr_kept"
    assert (tmp_path / "plugin-data" / "scalekit" / "identifier").read_text().strip() == "usr_kept"
    assert "Scalekit identifier created" not in capsys.readouterr().out
