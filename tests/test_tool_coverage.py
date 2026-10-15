import json

import pytest

from mgsv_mcp.catalog import Catalog
from mgsv_mcp.config import Config
from mgsv_mcp import supplements
from mgsv_mcp.knowledge import Knowledge, rebuild


def test_archive_versions_never_resolve_to_each_other(tmp_path):
    config = Config(root=tmp_path)
    config.data.mkdir()
    records = []
    for version in ["v0.2", "v0.5.3"]:
        exe = config.data / version / "GzsTool.exe"
        exe.parent.mkdir()
        exe.write_bytes(b"placeholder")
        records.append({"repo": "Atvaark/GzsTool", "version": version, "executables": [str(exe)]})
    manifest = config.data / "installed-tools.json"
    manifest.write_text(json.dumps(records))
    catalog = Catalog(config)
    assert catalog.executable("gzstool").parent.name == "v0.5.3"
    assert catalog.executable("gzstool-gz").parent.name == "v0.2"
    manifest.write_text(json.dumps(records[:1]))
    with pytest.raises(ValueError, match="not installed"):
        catalog.executable("gzstool")


def test_gui_presence_and_alias_do_not_imply_execution(tmp_path):
    config = Config(root=tmp_path)
    config.data.mkdir()
    exe = config.data / "FvTwool.exe"
    exe.write_bytes(b"placeholder")
    (config.data / "installed-tools.json").write_text(json.dumps([
        {"repo": "BobDoleOwndU/FvTwool", "executables": [str(exe)]}]))
    (config.data / "catalog.json").write_text(json.dumps([
        {"id": "fvtwool", "aliases": ["FV2 editor"], "install_probe": {
            "repository": "BobDoleOwndU/FvTwool", "executable": "FvTwool.exe"}}]))
    entry = Catalog(config).get("fv2 EDITOR")
    assert entry["installed"] is True
    assert entry["execution_supported"] is False
    exe.unlink()
    assert Catalog(config).get("fvtwool")["installed"] is False


def test_web_reference_refresh_does_not_fetch_or_claim_freshness(tmp_path, monkeypatch):
    config = Config(root=tmp_path)
    wiki = config.upstream / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "Test.md").write_text("# Test")
    monkeypatch.setattr("mgsv_mcp.knowledge.git", lambda *args: "wiki123")
    item = {"id": "publisher", "kind": "web-reference", "name": "Publisher",
            "url": "https://example.com", "summary": "HistoricalExtractor",
            "tags": ["Tools"], "origin": "user", "reviewed_at": "2026-10-10",
            "coverage_note": "Reviewed reference; installer not mirrored."}
    (tmp_path / "additional-resources.json").write_text(json.dumps({"schema_version": 1, "sources": [], "web_references": [item]}))
    def forbidden(*args):
        pytest.fail("Reference-only refresh must not perform network calls")
    monkeypatch.setattr(supplements.remote, "request", forbidden)
    result = supplements.refresh(config, "publisher")
    assert result["sources"][0]["status"] == "reference-only"
    inventory = supplements.inventory(config)[0]
    assert inventory["coverage"] == "curated-reference"
    assert inventory["retrieved_at"] is None
    assert inventory["reviewed_at"] == "2026-10-10"
    rebuild(config)
    doc = Knowledge(config).fetch("resource:publisher")
    assert "HistoricalExtractor" in doc["text"]
    assert doc["source_revision"] is None
    assert Catalog(config).get("publisher")["installed"] is None


def test_issue_titles_are_labeled_as_unverified_reports(tmp_path, monkeypatch):
    config = Config(root=tmp_path)
    config.data.mkdir()
    item = {"id": "repo:o/r", "kind": "repository", "name": "Tool", "repository": "o/r",
            "url": "https://github.com/o/r", "summary": "Tool documentation.", "tags": []}
    (tmp_path / "additional-resources.json").write_text(json.dumps({"schema_version": 1, "sources": [item]}))
    supplements.save_snapshot(config, item["id"], {"revision": "123", "retrieved_at": "2026-10-10",
        "issues": [{"title": "Example compatibility report", "url": "https://github.com/o/r/issues/1"}]})
    body = supplements.documents(config)[0]["body"]
    assert "not verified compatibility findings" in body
    assert "https://github.com/o/r/issues/1" in body


def test_portable_gui_matches_package_and_exact_version_without_github_repo(tmp_path):
    config = Config(root=tmp_path)
    config.data.mkdir()
    exe = config.data / "NinjaRipper.exe"
    exe.write_bytes(b"placeholder")
    record = {"package_id": "ninja-ripper-1.7.1", "version": "1.7.1", "executables": [str(exe)]}
    manifest = config.data / "installed-tools.json"
    manifest.write_text(json.dumps([record]))
    (config.data / "catalog.json").write_text(json.dumps([{"id": "ninja-ripper", "version": "1.7.1",
        "aliases": ["Ninja Ripper 1.7.1"], "install_probe": {"package_id": "ninja-ripper-1.7.1",
        "version": "1.7.1", "executable": "NinjaRipper.exe"}}]))
    catalog = Catalog(config)
    entry = catalog.get("Ninja Ripper 1.7.1")
    assert entry["installed"] and not entry["execution_supported"]
    assert entry["installed_packages"][0]["version"] == "1.7.1"
    # Non-GitHub records must not crash the ordinary adapter resolver.
    with pytest.raises(ValueError, match="not installed"):
        catalog.executable("gzstool")
    record["version"] = "2.0"
    manifest.write_text(json.dumps([record]))
    assert catalog.get("ninja-ripper")["installed"] is False


def test_package_docs_preserve_archive_provenance_through_reference_refresh(tmp_path, monkeypatch):
    config = Config(root=tmp_path)
    wiki = config.upstream / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "Test.md").write_text("# Test")
    monkeypatch.setattr("mgsv_mcp.knowledge.git", lambda *args: "wiki123")
    item = {"id": "ninja-ripper", "kind": "web-reference", "name": "Ninja Ripper 1.7.1",
            "url": "https://example.com/release", "summary": "Free legacy version", "tags": [],
            "origin": "user", "reviewed_at": "2026-10-10", "coverage_note": "Bundled docs only"}
    (tmp_path / "additional-resources.json").write_text(json.dumps({"schema_version": 1, "sources": [], "web_references": [item]}))
    snapshot = {"package_id": "ninja-ripper-1.7.1", "revision": "sha256:" + "a" * 64,
                "retrieved_at": "2026-10-10T00:00:00Z", "documents": [{"path": "help_en.txt",
                    "body": "LegacyRipExample", "url": "https://example.com/release.7z"}]}
    supplements.save_snapshot(config, item["id"], snapshot)
    supplements.refresh(config, item["id"])
    result = Knowledge(config).search("LegacyRipExample", kind="package-document")["results"][0]
    assert result["source_revision"] == snapshot["revision"]
    assert supplements.cached(config, item["id"]) == snapshot
    assert result["source_url"] == "https://example.com/release.7z"
