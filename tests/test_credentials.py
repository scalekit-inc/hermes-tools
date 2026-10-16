import importlib.util
from pathlib import Path

import pytest

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


def test_register_creates_an_identifier_and_keeps_it(tmp_path, capsys):
    first = register(ctx=object(), env=_values(), hermes_home=tmp_path)
    second = register(ctx=object(), env=_values(), hermes_home=tmp_path)
    shown = capsys.readouterr().out
    stored = tmp_path / "plugin-data" / "hermes-tools" / "identifier"

    assert first.startswith("usr_")
    assert second == first
    assert stored.read_text().strip() == first
    assert not (tmp_path / "plugins" / "hermes-tools" / "identifier").exists()
    assert first in shown
    assert shown.count(first) == 1


def test_register_refuses_to_load_when_a_credential_is_missing(tmp_path):
    with pytest.raises(RuntimeError, match="SCALEKIT_ENVIRONMENT_URL"):
        register(ctx=object(), env={}, hermes_home=tmp_path)

    assert list(tmp_path.rglob("identifier")) == []


def test_register_reads_the_process_environment_when_no_env_is_passed(monkeypatch, tmp_path):
    for name in REQUIRED_CREDENTIALS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="SCALEKIT_CLIENT_ID"):
        register(ctx=object(), hermes_home=tmp_path)
