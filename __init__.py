"""Wire the Scalekit plugin. Schemas, handlers, and Scalekit calls live in sibling modules."""

import importlib.util
from pathlib import Path


def _load_sibling(name):
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"hermes_tools_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_credentials = _load_sibling("credentials")
REQUIRED_CREDENTIALS = _credentials.REQUIRED_CREDENTIALS
missing_credential_message = _credentials.missing_credential_message
read_credentials = _credentials.read_credentials


def register(ctx, env=None, hermes_home=None):
    """Publish the tools. Hermes discovery passes no env, so this does not read secrets."""
    identifier = None
    if env is not None and _credentials.missing_credential_message(env) is None:
        identifier, _created = _credentials.load_or_create_identifier(hermes_home)
    if hasattr(ctx, "register_tool"):
        schemas = _load_sibling("schemas")
        tool_handlers = _load_sibling("tool_handlers")
        for schema in schemas.TOOLS:
            ctx.register_tool(
                schema["name"],
                "scalekit",
                schema,
                tool_handlers.HANDLERS[schema["name"]],
            )
        ctx.register_skill(
            "scalekit",
            Path(__file__).resolve().parent / "skills" / "scalekit" / "SKILL.md",
            "Rules for acting in an app through Scalekit.",
        )
        ctx.register_skill(
            "hermes-delegated-auth",
            Path(__file__).resolve().parent / "skills" / "hermes-delegated-auth" / "SKILL.md",
            "Act as a named user through Scalekit AgentKit.",
        )
    return identifier
