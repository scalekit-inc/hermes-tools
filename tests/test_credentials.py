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


def test_plugin_stops_and_names_each_missing_credential():
    message = missing_credential_message({})

    assert message is not None
    for name in REQUIRED_CREDENTIALS:
        assert name in message


def test_plugin_names_only_the_credential_that_is_missing():
    present = {name: "set" for name in REQUIRED_CREDENTIALS}
    present["SCALEKIT_CLIENT_SECRET"] = ""

    message = missing_credential_message(present)

    assert message is not None
    assert "SCALEKIT_CLIENT_SECRET" in message
    assert "SCALEKIT_CLIENT_ID" not in message


def test_complete_credentials_do_not_stop_the_plugin():
    present = {name: "set" for name in REQUIRED_CREDENTIALS}

    assert missing_credential_message(present) is None
    register(ctx=object(), env=present)


def test_register_refuses_to_load_when_a_credential_is_missing():
    with pytest.raises(RuntimeError, match="SCALEKIT_IDENTIFIER"):
        register(ctx=object(), env={})


def test_register_reads_the_process_environment_when_no_env_is_passed(monkeypatch):
    for name in REQUIRED_CREDENTIALS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="SCALEKIT_CLIENT_ID"):
        register(ctx=object())


def test_install_asks_for_the_four_scalekit_values():
    manifest = (_ROOT / "plugin.yaml").read_text()

    for name in REQUIRED_CREDENTIALS:
        assert f"name: {name}" in manifest
