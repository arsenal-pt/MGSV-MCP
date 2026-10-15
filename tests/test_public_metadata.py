from pathlib import Path
import ast
import tomllib
from mgsv_mcp import __version__
from mgsv_mcp.server import VERSION

def test_public_version_metadata_agrees():
    root = Path(__file__).resolve().parents[1]
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert VERSION == __version__ == metadata["project"]["version"] == (root / "VERSION").read_text().strip()

def test_public_server_exposes_expected_contract():
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "src/mgsv_mcp/server.py").read_text(encoding="utf-8"))
    tools = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and any(isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "tool" for d in n.decorator_list)]
    assert len(tools) == len(set(tools)) == 25
    assert {"prepare_tool_job", "run_tool_job", "search", "repository_source"} <= set(tools)
