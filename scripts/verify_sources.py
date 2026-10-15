"""Verify additional references through a real MCP stdio connection."""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]


def payload(result):
    values = [json.loads(c.text) for c in result.content if c.type == "text"]
    assert values, "Missing JSON tool content"
    return values[0] if len(values) == 1 else values


async def verify():
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")])
    checks = []
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            info = await client.initialize()
            tools = await client.list_tools()
            names = {t.name for t in tools.tools}
            assert {"list_additional_sources", "sync_additional_sources"} <= names
            async def call(name, args):
                response = await client.call_tool(name, args)
                assert not response.is_error, (name, response)
                return payload(response)
            sources = await call("list_additional_sources", {})
            primary = [s for s in sources if s["origin"] == "user"]
            assert len(primary) == 9
            for source in sources:
                assert source["cached"] or source["coverage"] == "curated-reference", source["id"]
                page = await call("fetch", {"id": "resource:" + source["id"]})
                assert page["source_id"] == source["id"]
                assert page["source_revision"] == source["revision"]
                entry = await call("get_modding_tool", {"tool_id": source["id"]})
                assert entry["additional_source"] is True
            checks.append("All configured sources are fetchable and catalogued; upstream snapshots and curated web references are distinguished")
            results = await call("search_wiki", {"query": "reload_scripts", "kind": "repository-document"})
            assert any(r["source_id"] == "repo:alicealys/tpp-server-emulator" for r in results["results"])
            checks.append("Emulator scripting documentation is searchable with its own source commit")
            versions = {"repo:joey35233/foxkit-3": "6000.0.47f1", "repo:youarebritish/foxkit": "2018.3.6f1"}
            for source_id, version in versions.items():
                doc = await call("fetch", {"id": "source:" + source_id + "/FoxKit/ProjectSettings/ProjectVersion.txt"})
                assert version in doc["text"]
                assert "/blob/" + doc["source_revision"] + "/" in doc["source_url"]
            checks.append("FoxKit project versions remain distinct and correctly attributed")
            soc = next(s for s in sources if s["id"] == "wiki:morbidslinky/soc")
            assert soc["cached_documents"] == 8
            pages = await call("list_wiki_pages", {"kind": "repository-document"})
            assert len([p for p in pages["pages"] if p["id"].startswith("source:wiki:morbidslinky/soc/")]) == 8
            checks.append("All eight SOC wiki guides are indexed")
            nucleus = next(s for s in sources if s["id"] == "repo:mxmstr/nucleusgamefixes")
            tree = await call("repository_source", {"tool_id": nucleus["id"], "path": "MGSVOPython", "ref": nucleus["revision"]})
            assert any(e["path"] == "MGSVOPython/CommandProcessor.py" for e in tree["entries"])
            checks.append("Source browsing works for newly supplied repositories")
            error = await client.call_tool("sync_additional_sources", {"source_id": "repo:not/configured"})
            assert error.is_error
            checks.append("Unknown source refresh returns a protocol error without fetching")
            status = await call("server_status", {})
            return {"verified_at": datetime.now(timezone.utc).isoformat(), "server_version": info.server_info.version,
                    "mcp_tools": len(names), "documents": status["wiki"]["pages"],
                    "catalog_entries": status["catalog_entries"], "checks": checks}


if __name__ == "__main__":
    result = asyncio.run(verify())
    (ROOT / "data/additional-sources-verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
