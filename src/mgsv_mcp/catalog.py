from __future__ import annotations

import json
import re
from urllib.parse import urlsplit

from .knowledge import links

# Commands are implementation-owned. Wiki content never becomes an executable command.
ADAPTERS = {
    "gzstool": {"exe":"GzsTool.exe", "repo":"Atvaark/GzsTool", "version":"v0.5.3", "page":"GzsTool", "extensions":[".dat",".fpk",".fpkd",".pftxs",".sbp",".xml"], "note":"Pinned to 0.5.3: the wiki warns about 0.6 repacking. Use gzstool-gz for Ground Zeroes .g0s files."},
    "gzstool-gz": {"exe":"GzsTool.exe", "repo":"Atvaark/GzsTool", "version":"v0.2", "page":"GzsTool", "extensions":[".g0s",".fpk",".fpkd",".pftxs",".xml"], "note":"Ground Zeroes archive adapter pinned to v0.2. Includes data_01.g0s and data_02.g0s; do not use for TPP .dat archives."},
    "gzstool-bob": {"exe":"GzsTool.exe", "repo":"BobDoleOwndU/GzsTool", "page":"GzsTool", "extensions":[".dat",".fpk",".fpkd",".pftxs",".sbp",".xml"], "note":"Bob's fork also provides hash debug operations."},
    "foxtool": {"exe":"FoxTool.exe", "repo":"Atvaark/FoxTool", "page":"FoxTool", "extensions":[".xml",".bnd",".clo",".des",".evf",".fox2",".fsd",".lad",".parts",".ph",".phsd",".sdf",".sim",".tgt",".vdp",".veh",".vfxlf"]},
    "ftextool": {"exe":"FtexTool.exe", "repo":"Atvaark/FtexTool", "page":"FtexTool", "extensions":[".ftex",".dds"], "note":"Stage all matching .ftexs siblings with the .ftex."},
    "langtool": {"exe":"LangTool.exe", "repo":"Atvaark/FoxEngine.TranslationTool", "page":"LangTool", "extensions":[".lng",".lng2",".xml"]},
    "subptool": {"exe":"SubpTool.exe", "repo":"Atvaark/FoxEngine.TranslationTool", "page":"SubpTool", "extensions":[".subp",".xml"]},
    "ffnttool": {"exe":"FfntTool.exe", "repo":"Atvaark/FoxEngine.TranslationTool", "page":"FfntTool", "extensions":[".ffnt",".xml"]},
    "fsmtool": {"exe":"FsmTool.exe", "repo":"BobDoleOwndU/FsmTool", "page":"FsmTool", "extensions":[".fsm",".xml"]},
    "mtartool": {"exe":"MtarTool.exe", "repo":"BobDoleOwndU/MtarTool", "page":"MtarTool", "extensions":[".mtar",".xml"]},
    "autopftxstool": {"exe":"AutoPftxsTool.exe", "repo":"BobDoleOwndU/AutoPftxsTool", "page":"AutoPftxsTool", "extensions":[".pftxs"], "directory":True},
    "fcnptool": {"exe":"FcnpTool.exe", "repo":"BobDoleOwndU/FcnpTool", "page":"FCNP", "extensions":[".fcnp",".xml"]},
    "grxarraytool": {"exe":"GrxArrayTool.exe", "repo":"kapuragu/GrxArrayTool", "page":"GRXLA", "extensions":[".grxla",".grxoc",".json"]},
    "rdftool": {"exe":"RdfTool.exe", "repo":"kapuragu/RdfTool", "page":"RDF", "extensions":[".rdf",".xml"]},
    "spchtool": {"exe":"SpchTool.exe", "repo":"kapuragu/SpchTool", "page":"SPCH", "extensions":[".spch",".xml"]},
    "stptool": {"exe":"StpTool.exe", "repo":"kapuragu/StpTool", "page":"Animation", "extensions":[".stp",".sab",".bnk"], "directory":True},
    "tcvptool": {"exe":"TcvpTool.exe", "repo":"kapuragu/TcvpTool", "page":"File_Formats", "extensions":[".tcvp",".xml"]},
    "traptool": {"exe":"TrapTool.exe", "repo":"kapuragu/TrapTool", "page":"TRAP", "extensions":[".trap",".xml"]},
    "lbatool": {"exe":"LbaTool.exe", "repo":"youarebritish/LbaTool", "page":"LBA", "extensions":[".lba",".xml"]},
    "vfxtool": {"exe":"VfxTool.exe", "repo":"youarebritish/VfxTool", "page":"VFX", "extensions":[".vfx",".xml"]},
}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build_catalog(config, documents):
    entries = {}
    def add(key, name, kind, doc, urls=(), context=""):
        entry = entries.setdefault(key, {"id":key, "name":name, "kind":kind,
            "wiki_pages":[], "source_pages":[], "urls":[], "evidence":[], "integration":"documentation"})
        origin_field = "source_pages" if doc.get("source_id", "mgsv-wiki") != "mgsv-wiki" else "wiki_pages"
        if doc["url"] not in entry[origin_field]:
            entry[origin_field].append(doc["url"])
        for url in urls:
            if url not in entry["urls"]:
                entry["urls"].append(url)
        if context and len(entry["evidence"]) < 8:
            entry["evidence"].append({"page_id":doc["id"], "text":context[:1200]})
        return entry
    for doc in documents:
        body = doc["body"]
        if "Tools" in doc["tags"] and doc["title"] not in {"Tools","File Tools","Fox","Links to Useful Github Repos"}:
            add(slug(doc["title"]), doc["title"], "wiki-tool-or-guide", doc,
                context=re.sub(r"{%.*?%}", "", body, flags=re.S).strip()[:1200])
        for match in re.finditer(r"{%\s*include infobox\s+(.*?)%}", body, re.S):
            attrs = dict(re.findall(r'(\w+)="(.*?)"', match.group(1), re.S))
            name = attrs.get("title", doc["title"])
            urls = re.findall(r'https?://[^\s"]+', attrs.get("site", "")+" "+attrs.get("download", ""))
            add(slug(name), name, "tool-or-framework", doc, urls, body[match.end():match.end()+1000])
        for link in links(body, doc["url"]):
            parts = urlsplit(link["url"])
            if parts.netloc.lower() == "github.com":
                path = parts.path.strip("/").split("/")
                if len(path) >= 2 and path[0].lower() not in {"features","topics","orgs","settings","user-attachments","sponsors","marketplace","collections"}:
                    repo = "/".join(path[:2]).removesuffix(".git")
                    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
                        continue
                    entry=add("repo:"+repo.lower(), repo, "linked-repository", doc,
                              ["https://github.com/"+repo], link["context"])
                    entry["repository"] = repo
            elif link["external"] and link["label"] and re.search(r"tool|editor|plugin|audacity|blender|hxd|ghidra|wwise|renderdoc|download", link["label"], re.I):
                add("link:"+slug(link["label"])+"-"+slug(parts.netloc), link["label"], "external-tool-link", doc, [link["url"]], link["context"])
    by_stem = {d["id"].split("/")[-1].removesuffix(".md"):d for d in documents}
    for adapter, info in ADAPTERS.items():
        doc = by_stem.get(info["page"])
        if doc:
            e=add(adapter, info["exe"].removesuffix(".exe")+(" (Bob fork)" if adapter.endswith("-bob") else " (Ground Zeroes v0.2)" if adapter == "gzstool-gz" else ""), "cli", doc, ["https://github.com/"+info["repo"]])
            e.update(integration="executable-adapter", adapter=adapter, repository=info["repo"],
                     pinned_version=info.get("version"),
                     extensions=info["extensions"], note=info.get("note",""))
            e["options"]={"ftextool":{"texture_type":["diffuse","material","normal","cube"],"texture_flags":["Default","Clp","Unknown"],"ftexs_files":"integer 0..3"},"mtartool":{"numbered":"boolean"},"subptool":{"language":["eng","rus","jpn","ara","por","fre","ger","spa","ita"]},"stptool":{"game":["TPP","GZ"],"output_game":["TPP","GZ"]}}.get(adapter,{})
    # These are named components inside a suite, not separate downloads.
    for name, parent in [(n,"File_Monolith") for n in ["Archive Unpacker","Mass Texture Converter","File Proliferator","Filename Updater","Archive Transferrer","Texture Aggregator","Regex File Copier"]]+[("MakeBite","SnakeBite_Mod_Manager")]:
        if parent in by_stem:
            add(slug(name),name,"gui-suite-component",by_stem[parent],context="Component of "+by_stem[parent]["title"])
    # Stable IDs merge supplied repos with wiki entries. Distinct forks remain distinct.
    from .supplements import inventory
    by_id = {d["id"]: d for d in documents}
    for source in inventory(config):
        doc = by_id["resource:" + source["id"]]
        entry = add(source["id"], source["name"], source["kind"], doc,
                    [source["url"]], source["summary"])
        entry.update(name=source["name"], additional_source=True,
                     source_kind=source["kind"], origin=source["origin"], tags=source["tags"],
                     summary=source["summary"], source_revision=source["revision"],
                     retrieved_at=source["retrieved_at"], metadata=source["metadata"],
                     cached_documents=source["cached_documents"],
                     discovered_repositories=source["discovered_repositories"])
        if source["kind"] == "repository":
            entry["repository"] = source["repository"]
        entry["coverage"] = source["coverage"]
    profile_path = config.root / "tool-profiles.json"
    if profile_path.exists():
        for tool_id, profile in json.loads(profile_path.read_text(encoding="utf-8")).items():
            if tool_id not in entries:
                raise ValueError("Tool profile has no catalog entry: " + tool_id)
            # Profiles document integration; executable command definitions remain in ADAPTERS.
            allowed = {"aliases", "repository", "capabilities", "requirements", "limitations",
                       "recommended_for", "related_tools", "install_probe", "reviewed_at", "version", "distribution"}
            if set(profile) - allowed:
                raise ValueError("Unsupported tool profile fields: " + tool_id)
            entries[tool_id].update(profile)
    catalog = sorted(entries.values(), key=lambda e:e["id"])
    (config.data/"catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False),encoding="utf-8")
    return catalog


class Catalog:
    def __init__(self,config):
        self.config=config

    def all(self):
        return json.loads((self.config.data/"catalog.json").read_text(encoding="utf-8"))

    def installed(self):
        path=self.config.data/"installed-tools.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def executable(self, adapter):
        from pathlib import Path
        if adapter not in ADAPTERS:
            raise ValueError("No executable adapter for this entry. Consult get_modding_tool for its documented setup.")
        custom=self.config.tools.get(adapter,{}).get("executable")
        if custom:
            path=Path(custom).resolve(strict=True)
            if path.suffix.lower() != ".exe" or not path.is_file():
                raise ValueError("Configure an existing native executable, not a shell script.")
            return path
        spec=ADAPTERS[adapter]
        for record in self.installed():
            if record.get("repo", "").lower() == spec["repo"].lower() and (not spec.get("version") or record["version"] == spec["version"]):
                for item in record["executables"]:
                    path=Path(item)
                    if not path.is_absolute():
                        path=self.config.root/path
                    if path.name.lower() == spec["exe"].lower() and path.is_file():
                        return path.resolve()
        raise ValueError(f"{adapter} is not installed. Run setup.ps1 or configure its executable in config.local.json.")

    def list(self,query="",offset=0,limit=50,kind=""):
        entries=[e for e in self.all() if (not query or query.lower() in json.dumps(e).lower()) and (not kind or e["kind"]==kind)]
        offset,limit=max(0,offset),max(1,min(limit,100))
        return {"total":len(entries),"tools":[{k:e[k] for k in ["id","name","kind","integration","wiki_pages","source_pages"]} for e in entries[offset:offset+limit]],"next_offset":offset+limit if offset+limit<len(entries) else None,
                "coverage_note":"Includes wiki tools, repository links, external tool links, suite components, supplied sources and cached discovery results. Linked repositories may be research, not runnable tools. external_resources exposes every indexed external link."}

    def get(self, tool_id):
        entries=self.all()
        entry=next((e for e in entries if e["id"].lower()==tool_id.lower()),None)
        if entry is None:
            matches=[e for e in entries if tool_id.lower() in [a.lower() for a in e.get("aliases",[])]]
            if len(matches)==1:
                entry=matches[0]
        if entry is None:
            raise ValueError("Unknown tool id. Use list_modding_tools.")
        entry=dict(entry)
        entry["execution_supported"] = bool(entry.get("adapter"))
        if entry.get("adapter"):
            try:
                entry.update(installed=True,executable=str(self.executable(entry["adapter"])))
            except ValueError as exc:
                entry.update(installed=False,setup=str(exc))
        else:
            entry["setup"]="Read the linked wiki guidance and publisher requirements. This entry has no verified automated adapter. GUI applications, Unity/Blender plugins and in-game frameworks need their own host/runtime."
            entry["installed"] = None
            entry["installation_note"] = "Installation is not tracked for this reference or host-dependent tool."
            if probe := entry.get("install_probe"):
                from pathlib import Path
                paths=[]
                packages=[]
                for record in self.installed():
                    identity_field = "package_id" if "package_id" in probe else "repo"
                    expected = probe.get("package_id", probe.get("repository", ""))
                    if not expected or record.get(identity_field, "").lower() != expected.lower():
                        continue
                    if probe.get("version") and record["version"] != probe["version"]:
                        continue
                    for value in record["executables"]:
                        path=Path(value)
                        path=path if path.is_absolute() else self.config.root/path
                        if path.name.lower()==probe["executable"].lower() and path.is_file():
                            paths.append(str(path.resolve()))
                    packages.append({k:record[k] for k in ["package_id", "version", "sha256", "source_page", "url", "install_root", "components"] if k in record})
                entry.update(installed=bool(paths),installed_executables=paths,
                             installed_packages=packages,
                             installation_note="Tracks downloaded executable presence only; GUI behavior has not been tested and is not automated.")
        return entry
