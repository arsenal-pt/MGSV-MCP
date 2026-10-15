import json
from pathlib import Path

import pytest

from mgsv_mcp.config import Config
from mgsv_mcp import workbench


def test_read_write_boundaries_and_optimistic_edit(tmp_path):
    config=Config(root=tmp_path)
    created=workbench.write_text(config,"project/script.lua","return {}\n")
    with pytest.raises(ValueError):workbench.write_text(config,"project/script.lua","oops")
    edited=workbench.write_text(config,"project/script.lua","return {x=1}\n",created["sha256"])
    assert "+return {x=1}" in edited["diff"]
    with pytest.raises(ValueError):config.writable("../outside.lua")
    with pytest.raises(ValueError):config.readable(str(tmp_path/"outside.lua"))


def test_reject_game_workspace_overlap(tmp_path):
    with pytest.raises(ValueError):Config(root=tmp_path,workspace=tmp_path/"game/lab",game_roots=[tmp_path/"game"])


def test_staging_preserves_source_and_texture_sidecars(tmp_path,monkeypatch):
    config=Config(root=tmp_path)
    config.workspace.mkdir()
    src=config.workspace/"sample.ftex";src.write_bytes(b"FTEX")
    (src.parent/"sample.1.ftexs").write_bytes(b"pixels")
    exe=tmp_path/"fake.exe";exe.write_bytes(b"trusted-placeholder")
    monkeypatch.setattr("mgsv_mcp.catalog.Catalog.executable",lambda self,key:exe)
    job=workbench.prepare(config,"ftextool",str(src))
    staged=Path(job["job_path"])/job["input"]
    assert staged.read_bytes()==b"FTEX"
    assert (staged.parent/"sample.1.ftexs").read_bytes()==b"pixels"
    assert src.read_bytes()==b"FTEX"
    with pytest.raises(ValueError):workbench.prepare(config,"ftextool",str(exe))


@pytest.mark.parametrize("xml",['<!DOCTYPE foo [<!ENTITY x SYSTEM "file:///secret">]><a/>','<Archive Name="C:\\game\\00.dat"/>','<File Path="../secret"/>'])
def test_xml_traversal_and_entities(tmp_path,xml):
    path=tmp_path/"a.xml";path.write_text(xml)
    with pytest.raises(ValueError):workbench.validate_xml(path)


def test_bad_job_ids_and_wrong_hash(tmp_path,monkeypatch):
    config=Config(root=tmp_path)
    with pytest.raises(ValueError):workbench.status(config,"../../x")
    config.workspace.mkdir()
    src=config.workspace/"a.ftex";src.write_bytes(b"FTEX")
    exe=tmp_path/"fake.exe";exe.write_bytes(b"before")
    monkeypatch.setattr("mgsv_mcp.catalog.Catalog.executable",lambda self,key:exe)
    job=workbench.prepare(config,"ftextool",str(src));exe.write_bytes(b"after")
    with pytest.raises(ValueError,match="Executable changed"):workbench.run(config,job["job_id"])


def test_xml_repack_requires_sidecar_root(tmp_path,monkeypatch):
    config=Config(root=tmp_path);config.workspace.mkdir()
    xml=config.workspace/"a.xml";xml.write_text("<LangFile/>")
    exe=tmp_path/"fake.exe";exe.write_bytes(b"x")
    monkeypatch.setattr("mgsv_mcp.catalog.Catalog.executable",lambda self,key:exe)
    with pytest.raises(ValueError,match="input_root"):workbench.prepare(config,"langtool",str(xml))


def test_xml_namespaces_and_engine_paths_are_valid(tmp_path):
    path=tmp_path/"a.xml"
    path.write_text('<LangFile xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><File Path="/Assets/test.fmdl"/></LangFile>')
    workbench.validate_xml(path)
    path.write_text('<Archive Name="/Windows/escape.dat"/>')
    with pytest.raises(ValueError):workbench.validate_xml(path)


def test_typed_options_reject_shell_arguments():
    assert workbench.command(Path("FtexTool.exe"),"ftextool",Path("normal.dds"),{"texture_type":"normal"})==["FtexTool.exe","-t","normal","normal.dds"]
    with pytest.raises(ValueError):workbench.command(Path("x.exe"),"ftextool",Path("x"),{"extra_args":"& cmd"})


def test_cannot_copy_workspace_into_its_own_job(tmp_path,monkeypatch):
    config=Config(root=tmp_path);config.workspace.mkdir()
    xml=config.workspace/"a.xml";xml.write_text("<LangFile/>")
    exe=tmp_path/"fake.exe";exe.write_bytes(b"x")
    monkeypatch.setattr("mgsv_mcp.catalog.Catalog.executable",lambda self,key:exe)
    with pytest.raises(ValueError,match="contains the job output"):
        workbench.prepare(config,"langtool",str(xml),str(config.workspace))
    assert not (config.workspace/"jobs").exists()
