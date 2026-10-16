"""Scalekit account values and the person id Hermes acts as."""

import os
import secrets
from pathlib import Path

REQUIRED_CREDENTIALS = (
    "SCALEKIT_CLIENT_ID",
    "SCALEKIT_CLIENT_SECRET",
    "SCALEKIT_ENVIRONMENT_URL",
)


def missing_credential_message(env):
    """Name each Scalekit value that is empty. Return None when all are set."""
    missing = [name for name in REQUIRED_CREDENTIALS if not env.get(name)]
    if not missing:
        return None
    return "Missing Scalekit credentials: " + ", ".join(missing)


def read_credentials(env=None, secret_reader=None):
    """Read the three Scalekit values. A passed mapping wins. Else use get_secret."""
    if env is not None:
        return env
    reader = secret_reader
    if reader is None:
        try:
            from agent.secret_scope import get_secret
            reader = get_secret
        except ImportError:
            reader = None
    values = {}
    for name in REQUIRED_CREDENTIALS:
        if reader is not None:
            values[name] = reader(name) or ""
        else:
            values[name] = ""
    return values


def _data_dir(hermes_home):
    if hermes_home is None:
        try:
            from plugins.plugin_storage import plugin_data_dir
            return plugin_data_dir("scalekit")
        except ImportError:
            hermes_home = os.environ.get("HERMES_HOME", Path.home() / ".hermes")
    path = Path(hermes_home) / "plugin-data" / "scalekit"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_or_create_identifier(hermes_home):
    """Return the stored person id. Create usr_<hex> the first time."""
    directory = _data_dir(hermes_home)
    path = directory / "identifier"
    current = path.read_text().strip() if path.is_file() else ""
    if current:
        return current, False
    old = directory.parent / "hermes-tools" / "identifier"
    previous = old.read_text() if old.is_file() else ""
    if previous.strip():
        path.write_text(previous if previous.endswith("\n") else previous + "\n")
        return previous.strip(), False
    created = "usr_" + secrets.token_hex(4)
    path.write_text(created + "\n")
    print(f"Scalekit identifier created: {created}", flush=True)
    return created, True
