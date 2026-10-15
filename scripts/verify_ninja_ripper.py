"""Verify Ninja Ripper installation/catalog through MCP without running its binaries."""
import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from verify_sources import payload

ROOT = Path(__file__).resolve().parents[1]
SHA256 = "19fb1f20d4f435a35056380bb07f3736467b1f30a0c727fb9c6a754897782d55"


async def verify():
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            info = await client.initialize()
            async def call(name, arguments):
                response = await client.call_tool(name, arguments)
                assert not response.is_error, (name, response)
                return payload(response)
            for alias in ["ninja-ripper", "Ninja Ripper 1.7.1", "ninja-ripper-1.7.1"]:
                entry = await call("get_modding_tool", {"tool_id": alias})
                assert entry["version"] == "1.7.1" and entry["installed"]
                assert entry["distribution"] == "free legacy public version"
                assert entry["execution_supported"] is False
                assert {Path(p).parent.name for p in entry["installed_executables"]} == {"x64", "x86"}
                assert entry["installed_packages"][0]["sha256"] == SHA256
            installed = json.loads((ROOT / "data/installed-tools.json").read_text(encoding="utf-8"))
            record = next(r for r in installed if r.get("package_id") == "ninja-ripper-1.7.1")
            for relative, expected in record["file_sha256"].items():
                assert hashlib.sha256((ROOT / record["install_root"] / relative).read_bytes()).hexdigest() == expected
            doc = await call("fetch", {"id": "source:ninja-ripper/help_en.txt"})
            assert doc["source_revision"] == "sha256:" + SHA256 and doc["kind"] == "package-document"
            assert "NINJA RIPPER" in doc["text"]
            results = await call("search_wiki", {"query": "Noesis", "kind": "package-document"})
            assert any(r["source_id"] == "ninja-ripper" for r in results["results"])
            workflow = await call("modding_workflow", {"topic": "ninja-ripper"})
            assert all(not r.get("search_required") for r in workflow["references"])
            status = await call("server_status", {})
            assert status["server_version"] == "0.3.2"
            assert len(status["executable_adapters"]) == 20
            assert all(a["installed"] for a in status["executable_adapters"].values())
            return {"verified_at": datetime.now(timezone.utc).isoformat(), "server_version": info.server_info.version,
                    "tool_version": entry["version"], "installed": True, "execution_supported": False,
                    "installed_executables": entry["installed_executables"], "archive_sha256": SHA256,
                    "files_verified": len(record["file_sha256"]), "documents": status["wiki"]["pages"],
                    "catalog_entries": status["catalog_entries"], "checks": [
                        "Free 1.7.1 aliases resolve to installed x64/x86 GUI files",
                        "All installed file hashes match recorded extraction evidence",
                        "Bundled help is searchable and cites the archive SHA-256",
                        "Manual capture workflow references resolve",
                        "All 20 existing converter adapters remain installed"],
                    "execution_note": "No Ninja Ripper executable, helper, importer, capture, injection or game process was run."}


if __name__ == "__main__":
    result = asyncio.run(verify())
    (ROOT / "data/ninja-ripper-verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
