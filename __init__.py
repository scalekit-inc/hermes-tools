"""Hermes plugin: the tools layer for any Scalekit connector."""

import os

REQUIRED_CREDENTIALS = (
    "SCALEKIT_CLIENT_ID",
    "SCALEKIT_CLIENT_SECRET",
    "SCALEKIT_ENVIRONMENT_URL",
    "SCALEKIT_IDENTIFIER",
)


def missing_credential_message(env):
    """Name each Scalekit value that is empty. Return None when all are set."""
    missing = [name for name in REQUIRED_CREDENTIALS if not env.get(name)]
    if not missing:
        return None
    return "Missing Scalekit credentials: " + ", ".join(missing)


def register(ctx, env=None):
    """Load the plugin. Stop, and name the missing value, before any Scalekit call."""
    del ctx
    message = missing_credential_message(os.environ if env is None else env)
    if message:
        raise RuntimeError(message)
