"""Audit expanded tool coverage and a synthetic Ground Zeroes archive via MCP."""
import asyncio
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mgsv_mcp.catalog import ADAPTERS, Catalog
from mgsv_mcp.config import Config
from verify_sources import payload


async def verify():
    config = Config.load()
    fixture = config.workspace / ("verification-gz-" + uuid.uuid4().hex[:8])
    folder = fixture / "synthetic"
    folder.mkdir(parents=True)
    original = b"Original MCP synthetic G0S payload - no game content.\n"
    (folder / "mcp_test.txt").write_bytes(original)
    xml = fixture / "synthetic.g0s.xml"
    xml.write_text('''<?xml version="1.0"?>
<ArchiveFile xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="GzsFile" Name="synthetic.g0s">
  <Entries><Entry Hash="12345" FilePath="mcp_test.txt" /></Entries>
</ArchiveFile>''', encoding="utf-8")
    original_xml = xml.read_bytes()
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")])
    checks = []
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            info = await client.initialize()
            async def call(name, args):
                result = await client.call_tool(name, args)
                assert not result.is_error, (name, result)
                return payload(result)
            tools = await client.list_tools()
            for name in ["FoxTool", "gzstool", "gzstool-gz", "MtarTool", "FsmTool", "FtexTool", "AutoPftxsTool"]:
                entry = await call("get_modding_tool", {"tool_id": name})
                assert entry["installed"] and entry["execution_supported"], name
            for name in ["File Monolith", "FMDL Studio V2", "Ninja Ripper", "MGSV QAR Tool", "Blender MTAR Tools", "wwiser"]:
                entry = await call("get_modding_tool", {"tool_id": name})
                assert not entry["execution_supported"], name
            gui = await call("get_modding_tool", {"tool_id": "FV2 editor"})
            assert gui["installed"] and not gui["execution_supported"]
            checks.append("CLI installation, GUI presence, documentation-only entries and aliases are distinguished")
            sources = await call("list_additional_sources", {})
            assert all(s["cached"] or s["coverage"] == "curated-reference" for s in sources)
            wiki = next(s for s in sources if s["id"] == "wiki:bobdoleowndu/fmdl-studio-v2")
            assert wiki["cached_documents"] == 8
            for source_id, query in [("repo:morbidslinky/filemonolith", "Texture Aggregator"),
                                     ("repo:mctrollin/fox_engine_mtar_tools_blender", "GANI"),
                                     ("repo:bnnm/wwiser", "wwiser")]:
                found = await call("search_wiki", {"query": query, "kind": "repository-document", "limit": 50})
                assert any(r["source_id"] == source_id for r in found["results"]), (source_id, found)
            checks.append("Author documentation is searchable; eight FMDL Studio wiki pages are cached")
            jobs = []
            async def convert(path, root=""):
                args = {"adapter": "gzstool-gz", "input_path": str(path)}
                if root:
                    args["input_root"] = str(root)
                job = await call("prepare_tool_job", args)
                result = await call("run_tool_job", {"job_id": job["job_id"]})
                assert result["state"] == "completed", result
                jobs.append(job["job_id"])
                return Path(result["job_path"]) / "input"
            packed = await convert(xml, fixture)
            archive = packed / "synthetic.g0s"
            assert archive.stat().st_size > len(original)
            unpacked = await convert(archive)
            files = [p for p in (unpacked / "synthetic").rglob("*") if p.is_file()]
            assert len(files) == 1, files
            assert files[0].read_bytes() == original
            repacked = await convert(unpacked / "synthetic.g0s.xml", unpacked)
            assert (repacked / "synthetic.g0s").read_bytes() == archive.read_bytes()
            assert (folder / "mcp_test.txt").read_bytes() == original and xml.read_bytes() == original_xml
            checks.append("G0S: XML/payload -> archive -> original payload/XML -> byte-identical archive; originals unchanged")
            catalog = Catalog(config)
            release_root = config.data / "tool-bin/Atvaark__GzsTool"
            assert catalog.executable("gzstool").relative_to(release_root).parts[0] == "v0.5.3"
            assert catalog.executable("gzstool-gz").relative_to(release_root).parts[0] == "v0.2"
            installed = {adapter: str(catalog.executable(adapter)) for adapter in ADAPTERS}
            status = await call("server_status", {})
            return {"verified_at": datetime.now(timezone.utc).isoformat(), "server_version": info.server_info.version,
                    "mcp_tools": len(tools.tools), "documents": status["wiki"]["pages"],
                    "catalog_entries": status["catalog_entries"], "additional_sources": len(sources),
                    "installed_adapters": len(installed), "checks": checks, "jobs": jobs,
                    "g0s_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                    "limits": "Synthetic single-entry fixture, without optional per-entry key header; no game-archive or in-game compatibility test."}


if __name__ == "__main__":
    result = asyncio.run(verify())
    (ROOT / "data/tool-audit-verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
