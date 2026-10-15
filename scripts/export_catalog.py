"""Export the current local catalog and additional source coverage as Markdown."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mgsv_mcp.catalog import Catalog
from mgsv_mcp.config import Config
from mgsv_mcp.knowledge import Knowledge
from mgsv_mcp.supplements import cached, inventory


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def export():
    config = Config.load()
    status = Knowledge(config).status()
    catalog = Catalog(config).all()
    lines = ["# MGSV tool and reference catalog", "",
             f"Snapshot exported from wiki commit `{status['revision']}` and cached additional sources. {len(catalog)} entries. Only **executable-adapter** entries have callable converters.", "",
             "| ID | Name | Integration | Evidence | Publisher/source |", "|---|---|---|---|---|"]
    for entry in catalog:
        evidence = (entry["wiki_pages"] + entry["source_pages"])[0]
        url = (entry["urls"] or [evidence])[0]
        lines.append(f"| {cell(entry['id'])} | {cell(entry['name'])} | {entry['integration']} | [Reference]({evidence}) | [Source]({url}) |")
    (config.root / "TOOL_CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    items = inventory(config)
    cached_count = sum(s["cached_documents"] for s in items)
    web_count = sum(s["kind"] == "web-reference" for s in items)
    lines = ["# Additional MGSV resources", "",
             "The supplied repositories and tool references are preserved in `additional-resources.json`, together with reviewed publisher sources and author wikis. This file describes the locally cached snapshot; use `list_additional_sources` for current retrieval times and coverage.", "",
             "Search the combined corpus with `search` or `search_wiki`. Fetch a source summary using `resource:<source-id>`. `repository_source` reads any catalogued repository at a cited commit; it does not compile or run that project.", "",
             f"The index includes {len(items)} configured sources and {cached_count} cached source documents. These can include repository text and documentation bundled in pinned packages. {web_count} web references provide reviewed descriptions and links; any bundled documents are identified by their archive hash. NucleusGameFixes has no root README; its MGSV directories are available through source browsing. Profiles and topic pages supply discovery metadata rather than full repository mirrors.", "",
             "Refresh GitHub sources with `python server.py sync-resources`, or select one source with `--source-id`. Wiki refreshes preserve these additions. Individual failures retain previous snapshots. Curated web references retain their actual review date; they are not scraped automatically. No emulator service or Unity/GUI editor is launched by indexing.", ""]
    for source in items:
        lines.extend([f"## {source['name']}", "", f"ID: `{source['id']}` · [Source]({source['url']})", "", source["summary"], "",
                      f"Origin: {source['origin']}. Cached documents: {source['cached_documents']}. Discovered repositories: {source['discovered_repositories']}.",
                      f"Coverage: `{source['coverage']}`. Retrieved: `{source['retrieved_at']}`. Revision (commit or package hash): `{source['revision'] or 'none'}`.", ""])
        if source["kind"] == "web-reference":
            lines.extend([f"Reviewed: {source['reviewed_at']}. {source['coverage_note']}", ""])
        snapshot = cached(config, source["id"])
        if snapshot.get("metadata") and source["kind"] == "repository":
            meta = snapshot["metadata"]
            lines.extend([f"Upstream description: {meta.get('description') or '(none)'}. Archived: {meta.get('archived')}. Default branch: `{meta.get('default_branch')}`.", ""])
        if source.get("include_pattern"):
            lines.extend([f"Profile relevance filter: `{source['include_pattern']}`. Unrelated projects are excluded from this profile listing.", ""])
        for doc in snapshot.get("documents", []):
            lines.append(f"- [{doc['path']}]({doc['url']}) — fetch ID: `source:{source['id']}/{doc['path']}`")
        if snapshot.get("documents"):
            lines.append("")
        if snapshot.get("repositories"):
            lines.append("Discovered repositories: " + ", ".join(f"[{r['full_name']}]({r['html_url']})" for r in snapshot["repositories"]) + ".")
            lines.append("")
    (config.root / "ADDITIONAL_RESOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Exported {len(catalog)} catalog entries and {len(items)} source records.")


if __name__ == "__main__":
    export()
