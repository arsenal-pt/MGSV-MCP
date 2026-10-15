import json
from pathlib import Path

import pytest

from mgsv_mcp.config import Config
from mgsv_mcp.knowledge import Knowledge,parse_document,rebuild,links


@pytest.fixture
def library(tmp_path,monkeypatch):
    config=Config(root=tmp_path)
    wiki=config.upstream/"wiki"; wiki.mkdir(parents=True)
    (wiki/"FtexTool.md").write_text('---\ntitle: FtexTool\npermalink: /FtexTool/\ntags: [Tools, Rendering]\nredirect_from: /OldTextureTool/\n---\nConvert FTEX textures.\n{% include infobox site="https://github.com/Atvaark/FtexTool" %}\n',encoding="utf-8")
    entity=wiki/"Entity_Reference/Fox/Route.txt";entity.parent.mkdir(parents=True)
    entity.write_text('<!--\ntitle: TppRouteSet\npermalink: /Entity_Reference/?/Fox/TppRouteSet/\ntags: []\n-->\n# Properties\nrouteId: 123\n',encoding="utf-8")
    (wiki/"Long.md").write_text('---\ntitle: Long\n---\n'+"\n".join(f"line {i}" for i in range(620)),encoding="utf-8")
    monkeypatch.setattr("mgsv_mcp.knowledge.git",lambda *args:"abc123")
    rebuild(config)
    return config,Knowledge(config)


def test_virtual_entities_and_frontmatter(library):
    _,kb=library
    result=kb.search("TppRouteSet",kind="entity")["results"][0]
    assert result["url"].endswith("?/Fox/TppRouteSet/")
    page=kb.fetch(result["id"])
    assert "routeId: 123" in page["text"]
    assert page["source_revision"]=="abc123"


def test_search_category_and_literal_input(library):
    _,kb=library
    assert kb.search("FtexTool",category="Rendering")["results"][0]["title"]=="FtexTool"
    assert not kb.search('FtexTool" OR *',category="Nonexistent")["results"]
    with pytest.raises(ValueError):kb.search("***")


def test_alias_pagination_and_categories(library):
    _,kb=library
    assert kb.fetch("/OldTextureTool/")["title"]=="FtexTool"
    assert kb.fetch("Long",1,500)["next_line"]==501
    assert kb.fetch("Long",501,500)["next_line"] is None
    assert kb.list_pages(kind="entity")["total"]==1
    assert any(x["category"]=="Rendering" for x in kb.categories())


def test_failed_rebuild_preserves_existing_index(library):
    config,kb=library
    (config.upstream/"wiki/broken.md").write_text('---\ntags: [unterminated\n---\n')
    with pytest.raises(Exception):rebuild(config)
    assert kb.status()["pages"]==3
    assert kb.fetch("FtexTool")["title"]=="FtexTool"


def test_external_inventory_and_generated_catalog(library):
    config,kb=library
    assert kb.external_resources("Atvaark")["total"]==1
    entries=json.loads((config.data/"catalog.json").read_text())
    assert any(e["id"]=="repo:atvaark/ftextool" for e in entries)
    assert any(e["id"]=="ftextool" and e["integration"]=="executable-adapter" for e in entries)


def test_links_with_spaces():
    found=list(links('[Image](/assets/My File.png) and <https://github.com/a/b>',"https://mgsvmoddingwiki.github.io/"))
    assert any(x["url"].endswith("My File.png") for x in found)


def test_markdown_repository_followed_by_colon_is_not_duplicated():
    found=list(links('[Repo](https://github.com/Owner/Repo): description',"https://example.com/"))
    assert [item["url"] for item in found] == ["https://github.com/Owner/Repo"]
