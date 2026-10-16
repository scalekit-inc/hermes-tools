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
    """Load the plugin. Stop, and name the missing value, before any Scalekit call."""
    credentials = _credentials
    source = credentials.read_credentials(env)
    message = credentials.missing_credential_message(source)
    if message:
        raise RuntimeError(message)
    identifier, created = credentials.load_or_create_identifier(hermes_home)
    if created:
        print(f"Scalekit identifier created: {identifier}", flush=True)
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
    return identifier
