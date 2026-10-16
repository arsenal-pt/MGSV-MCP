import json
from pathlib import Path

import pytest

from mgsv_mcp.config import Config
from mgsv_mcp.knowledge import Knowledge, rebuild
from mgsv_mcp import supplements
from mgsv_mcp.workflows import workflow


def _library(tmp_path, monkeypatch, entries):
    config = Config(root=tmp_path)
    wiki = config.upstream / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "Test.md").write_text("# Fixture\n", encoding="utf-8")
    monkeypatch.setattr("mgsv_mcp.knowledge.git", lambda *args: "wiki-fixture")
    (tmp_path / "additional-resources.json").write_text(
        json.dumps({"schema_version": 1, "sources": [], "web_references": entries}), encoding="utf-8")
    return config


def _entries():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "additional-resources.json").read_text(encoding="utf-8"))
    return [s for s in data["web_references"] if s["id"] in {
        "choc-adding-player-motions", "bobdoleowndu-bossquiet2-layers-notes"}]


def test_animation_references_are_searchable_with_their_own_pins(tmp_path, monkeypatch):
    entries = _entries()
    assert len(entries) == 2
    config = _library(tmp_path, monkeypatch, entries)
    rebuild(config)
    kb = Knowledge(config)
    inventory = {s["id"]: s for s in supplements.inventory(config)}
    for entry in entries:
        key = "resource:" + entry["id"]
        doc = kb.fetch(key)
        assert doc["source_revision"] == entry["reviewed_revision"]
        assert inventory[entry["id"]]["revision"] == entry["reviewed_revision"]
        assert doc["source_url"] == entry["reviewed_source_url"]
        assert "curated summary" in doc["content_note"]
        assert entry["reviewed_at"] in doc["text"]
        assert any(r["id"] == key for r in kb.search(entry["name"])["results"])
    plan = workflow(kb, "animations")
    assert {r.get("id") for r in plan["references"]} >= {"resource:" + e["id"] for e in entries}
    assert "not a claim" in plan["note"]
    assert any("NPC compatibility" in step for step in plan["steps"])


def test_legacy_unpinned_web_reference_remains_usable(tmp_path, monkeypatch):
    entry = {"id": "legacy", "kind": "web-reference", "name": "Legacy note",
             "url": "https://example.test/guide", "origin": "fixture", "tags": [], "summary": "Old authored note",
             "reviewed_at": "2020-01-01", "coverage_note": "A link only"}
    config = _library(tmp_path, monkeypatch, [entry])
    rebuild(config)
    doc = Knowledge(config).fetch("resource:legacy")
    assert doc["source_revision"] is None
    assert doc["source_url"] == entry["url"]
    assert doc["retrieved_at"] is None


@pytest.mark.parametrize("change, message", [
    ({"reviewed_source_url": "file:///private/note"}, "HTTPS"),
    ({"reviewed_source_url": ""}, "together"),
    ({"reviewed_revision": ""}, "together"),
])
def test_reviewed_source_provenance_rejects_incomplete_or_non_web_pairs(tmp_path, monkeypatch, change, message):
    entry = _entries()[0] | change
    config = _library(tmp_path, monkeypatch, [entry])
    with pytest.raises(ValueError, match=message):
        supplements.sources(config)
