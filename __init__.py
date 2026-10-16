"""Hermes plugin: the tools layer for any Scalekit connector."""

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


def _identifier_file(home):
    return Path(home) / "plugins" / "hermes-tools" / "identifier"


def load_or_create_identifier(home):
    """Return the stored identifier. Create usr_<hex> on the first call."""
    path = _identifier_file(home)
    if path.exists():
        current = path.read_text().strip()
        if current:
            return current, False
    created = "usr_" + secrets.token_hex(4)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(created + "\n")
    return created, True


def register(ctx, env=None, home=None):
    """Load the plugin. Stop, and name the missing value, before any Scalekit call."""
    del ctx
    source = os.environ if env is None else env
    message = missing_credential_message(source)
    if message:
        raise RuntimeError(message)
    root = Path(home) if home is not None else Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    identifier, created = load_or_create_identifier(root)
    if created:
        print(f"Scalekit identifier created: {identifier}", flush=True)
    return identifier
