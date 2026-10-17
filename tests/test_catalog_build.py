"""Rules from the Hermes catalog review on NousResearch/hermes-agent#140032."""

import importlib.util
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("hermes_tools_plugin", _ROOT / "__init__.py")
plugin = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(plugin)


def _shipped_files():
    for path in _ROOT.rglob("*"):
        parts = path.relative_to(_ROOT).parts
        if path.is_file() and parts[0] not in {".git", ".venv", "tests"} and "__pycache__" not in parts:
            if path.suffix in {".py", ".md", ".toml", ".yaml"}:
                yield path


def test_no_shipped_file_reads_a_dotenv_file():
    for path in _shipped_files():
        text = path.read_text()
        assert "load_dotenv" not in text, path
        assert "TOOL_CLIENT_ID" not in text, path


def test_no_shipped_file_prints_access_tokens():
    for path in _shipped_files():
        assert "get-authorization" not in path.read_text(), path


def test_the_authstack_skill_copy_is_not_in_the_plugin():
    assert not (_ROOT / "skills" / "hermes-delegated-auth").exists()


class _Ctx:
    def __init__(self):
        self.skills = []

    def register_tool(self, *args):
        pass

    def register_skill(self, name, *args):
        self.skills.append(name)


def test_register_bundles_only_the_scalekit_skill():
    ctx = _Ctx()
    plugin.register(ctx)
    assert ctx.skills == ["scalekit"]


def test_the_plugin_does_not_import_the_scalekit_sdk():
    for path in _shipped_files():
        if path.suffix == ".py":
            assert not re.search(r"^\s*(import|from) scalekit\b", path.read_text(), re.M), path


def test_the_readme_does_not_install_packages_into_the_hermes_python():
    readme = (_ROOT / "README.md").read_text()
    assert "pip install" not in readme
    assert "setuptools" not in readme
