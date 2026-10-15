import json
from urllib.error import HTTPError

import pytest

from mgsv_mcp.catalog import Catalog
from mgsv_mcp.config import Config
from mgsv_mcp.knowledge import Knowledge, rebuild
from mgsv_mcp import supplements


@pytest.fixture
def extra_library(tmp_path, monkeypatch):
    config = Config(root=tmp_path)
    wiki = config.upstream / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "Test.md").write_text("# Test\nSee https://github.com/Owner/Repo\n", encoding="utf-8")
    monkeypatch.setattr("mgsv_mcp.knowledge.git", lambda *args: "wiki123")
    item = {"id": "repo:owner/repo", "kind": "repository", "repository": "Owner/Repo",
            "name": "Example resource", "url": "https://github.com/Owner/Repo", "origin": "user",
            "tags": ["Server Emulation"], "summary": "Curated backend reference."}
    (tmp_path / "additional-resources.json").write_text(json.dumps({"schema_version": 1, "sources": [item]}))
    snapshot = {"source_id": item["id"], "revision": "other456", "retrieved_at": "2026-10-07T00:00:00Z",
                "metadata": {"full_name": "Owner/Repo", "archived": True},
                "documents": [{"path": "README.md", "body": "# Lua backend scripting\nDistinctiveSymbol\n",
                               "url": "https://github.com/Owner/Repo/blob/other456/README.md"}]}
    supplements.save_snapshot(config, item["id"], snapshot)
    rebuild(config)
    return config, item, snapshot


def test_wiki_rebuild_preserves_sources_and_their_own_provenance(extra_library):
    config, item, _ = extra_library
    rebuild(config)
    kb = Knowledge(config)
    result = kb.search("DistinctiveSymbol")["results"][0]
    assert result["source_revision"] == "other456"
    assert result["source_id"] == item["id"]
    doc = kb.fetch(result["id"])
    assert doc["source_url"].endswith("/other456/README.md")
    assert doc["retrieved_at"] == "2026-10-07T00:00:00Z"
    assert kb.fetch("wiki/Test.md")["source_revision"] == "wiki123"
    assert "curated summary" in kb.fetch("resource:" + item["id"])["content_note"]
    assert kb.list_pages(kind="repository-document")["total"] == 1


def test_additions_merge_with_existing_repository_entry(extra_library):
    config, item, _ = extra_library
    entries = Catalog(config).all()
    matches = [e for e in entries if e["id"] == item["id"]]
    assert len(matches) == 1
    assert matches[0]["wiki_pages"] and matches[0]["source_pages"]
    assert matches[0]["metadata"]["archived"] is True
    assert matches[0]["integration"] == "documentation"


def test_failed_refresh_keeps_previous_document_cache_and_index(extra_library, monkeypatch):
    config, item, snapshot = extra_library
    def fail(_):
        raise HTTPError("https://api.github.com", 403, "Rate limit", {}, None)
    monkeypatch.setattr(supplements, "repository_snapshot", fail)
    result = supplements.refresh(config, item["id"])
    assert result["sources"][0]["status"] == "error"
    assert result["sources"][0]["previous_snapshot_retained"] is True
    assert supplements.cached(config, item["id"]) == snapshot
    assert Knowledge(config).search("DistinctiveSymbol")["results"]


def test_refresh_updates_search_and_unknown_ids_do_not_fetch(extra_library, monkeypatch):
    config, item, snapshot = extra_library
    snapshot["documents"][0]["body"] = "NewBackendSymbol"
    snapshot["revision"] = "new789"
    monkeypatch.setattr(supplements, "repository_snapshot", lambda _: snapshot)
    result = supplements.refresh(config, item["id"])
    assert result["sources"][0]["status"] == "updated"
    assert Knowledge(config).search("NewBackendSymbol")["results"][0]["source_revision"] == "new789"
    assert not Knowledge(config).search("DistinctiveSymbol")["results"]
    with pytest.raises(ValueError, match="Unknown source"):
        supplements.refresh(config, "repo:not/configured")


def test_profile_pagination_and_relevance_filter(monkeypatch):
    calls = []
    def api(path):
        calls.append(path)
        if "page=2&" in path:
            return [{"full_name": "Author/FoxLib", "description": "Fox Engine library"}]
        return [{"full_name": f"Author/Unrelated{i}", "description": "Other project"} for i in range(100)]
    monkeypatch.setattr(supplements, "api", api)
    result = supplements.discovery_snapshot({"kind": "github-profile", "owner": "Author", "include_pattern": "fox"})
    assert len(calls) == 2
    assert result["observed_count"] == 101
    assert [r["full_name"] for r in result["repositories"]] == ["Author/FoxLib"]
    assert result["truncated"] is False


def test_topic_reports_incomplete_api_results(monkeypatch):
    monkeypatch.setattr(supplements, "api", lambda _: {"items": [], "total_count": 8, "incomplete_results": True})
    result = supplements.discovery_snapshot({"kind": "github-topic", "topic": "mgsv"})
    assert result["incomplete_results"] is True
    assert result["reported_total"] == 8


def test_repository_docs_are_pinned_and_missing_readme_is_supported(monkeypatch):
    def api(path):
        if "/commits/" in path:
            return {"sha": "commit123"}
        if "/readme?" in path:
            raise HTTPError(path, 404, "Not found", {}, None)
        return {"default_branch": "main", "full_name": "Owner/Repo"}
    urls = []
    def request(url):
        urls.append(url)
        return b"m_EditorVersion: test"
    monkeypatch.setattr(supplements, "api", api)
    monkeypatch.setattr(supplements.remote, "request", request)
    result = supplements.repository_snapshot({"repository": "Owner/Repo", "documents": ["Project/Version.txt"]})
    assert result["revision"] == "commit123"
    assert result["readme_found"] is False
    assert urls == ["https://raw.githubusercontent.com/Owner/Repo/commit123/Project/Version.txt"]
    assert result["documents"][0]["url"].endswith("/blob/commit123/Project/Version.txt")


def test_manifest_rejects_path_traversal(extra_library):
    config, item, _ = extra_library
    item["documents"] = ["../outside.txt"]
    (config.root / "additional-resources.json").write_text(json.dumps({"schema_version": 1, "sources": [item]}))
    with pytest.raises(ValueError, match="repository-relative"):
        supplements.sources(config)
