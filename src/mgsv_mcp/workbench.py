from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from .catalog import ADAPTERS, Catalog

_run_lock = threading.Lock()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect(config, path):
    p=config.readable(path)
    if not p.is_file():
        raise ValueError("Expected a file.")
    with p.open("rb") as stream:
        header=stream.read(64)
    return {"path":str(p),"size":p.stat().st_size,"sha256":digest(p),"header_hex":header.hex(),
            "header_ascii":"".join(chr(b) if 32<=b<127 else "." for b in header),
            "extension":p.suffix.lower(),"candidate_adapters":[k for k,v in ADAPTERS.items() if p.suffix.lower() in v["extensions"]]}


def validate_tree(source):
    # Reject links before copying so input cannot pull unrelated files into a job.
    paths=[source]
    total=0
    while paths:
        p=paths.pop()
        if p.is_symlink() or (hasattr(p,"is_junction") and p.is_junction()):
            raise ValueError("Symlinks/junctions are not accepted in staged inputs.")
        if getattr(p.lstat(),"st_file_attributes",0)&0x400:
            raise ValueError("Reparse points are not accepted in staged inputs.")
        if p.is_dir():
            paths.extend(p.iterdir())
        elif p.is_file():
            total+=p.stat().st_size
    return total


def validate_xml(path):
    if path.stat().st_size > 64*1024*1024:
        raise ValueError("XML input exceeds 64 MiB.")
    text=path.read_text(encoding="utf-8-sig")
    if re.search(r"<!DOCTYPE|<!ENTITY",text,re.I):
        raise ValueError("External XML entities are not accepted.")
    # Engine asset references /Assets/... are normal; OS drives, UNC paths,
    # and parent traversal in archive manifests are not.
    if re.search(r"(?:(?<![A-Za-z0-9])[A-Za-z]:[\\/]|\\\\|(?:^|[\s\"'>/\\])\.\.[/\\])",text):
        raise ValueError("XML contains an absolute OS path or parent traversal.")
    tree=ET.fromstring(text)
    if tree.attrib.get("Name","").startswith(("/","\\")):
        raise ValueError("Root archive output Name must be relative.")
    for node in tree.iter():
        for key,value in node.attrib.items():
            if key.lower() in {"name","filename","filepath","path","directory","outputpath"} and value.startswith(("/","\\")) and not value.startswith("/Assets/"):
                raise ValueError("XML contains a rooted filesystem path.")


def command(exe,adapter,staged,options=None):
    options=options or {}
    args=[str(exe)]
    if adapter=="ftextool":
        allowed={"texture_type","texture_flags","ftexs_files"}
        if "texture_type" in options:
            if options["texture_type"] not in {"diffuse","material","normal","cube"}:
                raise ValueError("texture_type must be diffuse, material, normal or cube.")
            args += ["-t",options["texture_type"]]
        if "texture_flags" in options:
            if options["texture_flags"] not in {"Default","Clp","Unknown"}:
                raise ValueError("texture_flags must be Default, Clp or Unknown.")
            args += ["-fl",options["texture_flags"]]
        if "ftexs_files" in options:
            if type(options["ftexs_files"]) is not int or not 0<=options["ftexs_files"]<=3:
                raise ValueError("ftexs_files must be an integer from 0 to 3.")
            args += ["-f",str(options["ftexs_files"])]
    elif adapter=="mtartool":
        allowed={"numbered"}
        if "numbered" in options and type(options["numbered"]) is not bool:
            raise ValueError("numbered must be boolean.")
    elif adapter=="subptool":
        allowed={"language"}
        if "language" in options:
            if options["language"] not in {"eng","rus","jpn","ara","por","fre","ger","spa","ita"}:
                raise ValueError("Unsupported subtitle language.")
            args += ["-"+options["language"]]
    elif adapter=="stptool":
        allowed={"game","output_game"}
        for name,flag in [("game","-gz"),("output_game","-outgz")]:
            if name in options:
                if options[name] not in {"TPP","GZ"}:
                    raise ValueError(name+" must be TPP or GZ.")
                if options[name]=="GZ":
                    args.append(flag)
    else:
        allowed=set()
    if set(options)-allowed:
        raise ValueError("Unsupported options for this adapter: "+", ".join(sorted(set(options)-allowed)))
    args.append(str(staged))
    if adapter=="mtartool" and options.get("numbered"):
        args.append("-n")
    return args


def prepare(config,adapter,input_path,input_root="",options=None):
    if adapter not in ADAPTERS:
        raise ValueError("Choose an executable adapter from list_modding_tools.")
    exe=Catalog(config).executable(adapter)
    source=config.readable(input_path)
    spec=ADAPTERS[adapter]
    command(exe,adapter,source,options)
    if source.is_dir() and not spec.get("directory"):
        raise ValueError("This adapter requires an individual file.")
    if source.is_file() and source.suffix.lower() not in spec["extensions"]:
        raise ValueError("Unsupported extension; expected "+", ".join(spec["extensions"]))
    source_root=config.readable(input_root) if input_root else None
    if source_root and (not source_root.is_dir() or not source.is_relative_to(source_root)):
        raise ValueError("input_root must be a directory containing input_path.")
    if source.suffix.lower()==".xml" and not source_root:
        raise ValueError("For XML repacking supply input_root containing the manifest and all sidecar files.")
    copy_source=source_root or source
    job_id=uuid.uuid4().hex
    job=config.writable("jobs/"+job_id)
    if copy_source.is_dir() and job.is_relative_to(copy_source):
        raise ValueError("Input directory contains the job output directory. Use a dedicated source subfolder, not the whole workbench.")
    size=validate_tree(copy_source)
    config.workspace.mkdir(parents=True,exist_ok=True)
    if size > shutil.disk_usage(config.workspace).free * 0.8:
        raise ValueError("Insufficient free space to stage this input and produce outputs.")
    job.mkdir(parents=True)
    inputs=job/"input"; inputs.mkdir()
    if source_root:
        shutil.copytree(source_root,inputs,dirs_exist_ok=True)
        staged=inputs/source.relative_to(source_root)
    elif source.is_dir():
        staged=inputs/source.name
        shutil.copytree(source,staged)
    else:
        staged=inputs/source.name
        shutil.copy2(source,staged)
        if source.suffix.lower()==".ftex":
            for sidecar in source.parent.glob(source.stem+"*.ftexs"):
                validate_tree(sidecar)
                shutil.copy2(sidecar,inputs/sidecar.name)
    for p in inputs.rglob("*.xml"):
        validate_xml(p)
    record={"job_id":job_id,"adapter":adapter,"input":str(staged.relative_to(job)),
            "original_input":str(source),"executable_sha256":digest(exe),
            "state":"prepared","staged_bytes":size,"options":options or {},
            "note":"Local trusted converter process; staging is not an operating-system security sandbox."}
    (job/"job.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
    return {**record,"job_path":str(job),"command_preview":command(exe,adapter,staged,options),
            "next":"run_tool_job(job_id) executes this staged copy. Read and edit staged files before running if needed."}


def job_path(config,job_id):
    if not re.fullmatch(r"[0-9a-f]{32}",job_id):
        raise ValueError("Invalid job id.")
    return config.writable("jobs/"+job_id,exists=True)


def run(config,job_id,timeout_seconds=120):
    with _run_lock:
        job=job_path(config,job_id)
        manifest=job/"job.json"
        record=json.loads(manifest.read_text(encoding="utf-8"))
        if record["state"]!="prepared":
            raise ValueError("This job has already run. Prepare a new job from its outputs for the next operation.")
        adapter=record["adapter"]
        exe=Catalog(config).executable(adapter)
        if digest(exe)!=record["executable_sha256"]:
            raise ValueError("Executable changed after preparation; prepare a fresh job.")
        staged=(job/record["input"]).resolve(strict=True)
        if not staged.is_relative_to(job/"input"):
            raise ValueError("Staged input escaped job directory.")
        validate_tree(job/"input")
        for p in (job/"input").rglob("*.xml"):
            validate_xml(p)
        before={str(p.relative_to(job)):digest(p) for p in (job/"input").rglob("*") if p.is_file()}
        record["state"]="running"
        manifest.write_text(json.dumps(record,indent=2),encoding="utf-8")
        try:
            # Some converters write hash dictionaries or stack traces beside their
            # executable; give every job its own runtime and all normal sidecars.
            runtime=job/"runtime";runtime.mkdir()
            for p in exe.parent.iterdir():
                if p.is_file():
                    validate_tree(p)
                    if p.stat().st_size>64*1024*1024:
                        raise ValueError("Runtime companion exceeds 64 MiB; use a dedicated tool installation folder.")
                    shutil.copy2(p,runtime/p.name)
            definitions=exe.parent/"Definitions"
            if definitions.is_dir():
                validate_tree(definitions)
                shutil.copytree(definitions,runtime/"Definitions")
            for p in exe.parent.glob("*.txt"):
                if p.stat().st_size<64*1024*1024:
                    target=job/"input"/p.name
                    if not target.exists():
                        shutil.copy2(p,target)
            before={str(p.relative_to(job)):digest(p) for p in (job/"input").rglob("*") if p.is_file()}
            with (job/"stdout.log").open("wb") as out,(job/"stderr.log").open("wb") as err:
                process=subprocess.run(command(runtime/exe.name,adapter,staged,record.get("options")),cwd=job/"input",stdin=subprocess.DEVNULL,
                    stdout=out,stderr=err,timeout=max(1,min(timeout_seconds,600)),shell=False,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
            record.update(state="completed" if process.returncode==0 else "failed",returncode=process.returncode)
        except subprocess.TimeoutExpired:
            record.update(state="timed_out",returncode=None)
        except (OSError,ValueError) as exc:
            record.update(state="failed",returncode=None,error=str(exc))
        after={str(p.relative_to(job)):digest(p) for p in (job/"input").rglob("*") if p.is_file()}
        record["changed_files"]=[{"path":p,"sha256":sha,"kind":"created" if p not in before else "modified"}
                                 for p,sha in after.items() if before.get(p)!=sha]
        record["deleted_files"]=[p for p in before if p not in after]
        record["outputs_verified"]=False
        stacktrace=job/"runtime/stacktrace.txt"
        if stacktrace.exists() and stacktrace.stat().st_size:
            record.update(state="failed",error=stacktrace.read_text(encoding="utf-8",errors="replace")[:8000])
        if record["state"]=="completed" and not record["changed_files"]:
            record["warning"]="Process exited zero but produced no new/changed staged files. Do not assume conversion succeeded."
        manifest.write_text(json.dumps(record,indent=2),encoding="utf-8")
        return status(config,job_id)


def status(config,job_id):
    job=job_path(config,job_id)
    record=json.loads((job/"job.json").read_text(encoding="utf-8"))
    record["job_path"]=str(job)
    for name in ["stdout","stderr"]:
        p=job/(name+".log")
        if p.exists():
            with p.open("rb") as f:
                f.seek(max(0,p.stat().st_size-12000))
                record[name]=f.read().decode("utf-8",errors="replace")
    return record


def hash_name(config,value,mode="filename"):
    flags={"filename":"-h","extension":"-he","with_extension":"-hwe","legacy":"-hl"}
    if mode not in flags or not value or len(value)>4096 or "\x00" in value:
        raise ValueError("Choose filename, extension, with_extension or legacy and a nonempty value.")
    exe=Catalog(config).executable("gzstool-bob")
    result=subprocess.run([str(exe),"-d",flags[mode],value],capture_output=True,text=True,
        errors="replace",timeout=15,stdin=subprocess.DEVNULL,shell=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
    output=result.stdout.strip()
    if result.returncode or not re.fullmatch(r"[0-9a-fA-F]+",output):
        raise RuntimeError("GzsTool hash failed: "+(result.stderr or result.stdout)[-2000:])
    return {"input":value,"mode":mode,"hash_hex":output,"tool":"BobDoleOwndU/GzsTool",
            "source_note":"Uses -hwe confirmed in upstream Program.cs; wiki table currently omits that hyphen."}


def read_text(config,path,start_line=1,max_lines=200):
    p=config.readable(path)
    if p.stat().st_size>8*1024*1024:
        raise ValueError("Text file exceeds 8 MiB; use a dedicated editor.")
    lines=p.read_text(encoding="utf-8-sig").splitlines()
    start=max(1,start_line); end=min(len(lines),start-1+max(1,min(max_lines,500)))
    return {"path":str(p),"sha256":digest(p),"total_lines":len(lines),
            "text":"\n".join(f"{i+1}: {lines[i]}" for i in range(start-1,end)),
            "next_line":end+1 if end<len(lines) else None}


def write_text(config,path,text,expected_sha256=""):
    p=config.writable(path)
    if p.suffix.lower() not in {".lua",".xml",".json",".md",".txt",".py",".cs",".h",".cpp",".toml"}:
        raise ValueError("Only source, configuration and documentation text extensions are supported.")
    if len(text.encode())>2*1024*1024:
        raise ValueError("Text exceeds 2 MiB.")
    if p.exists() and (not expected_sha256 or digest(p)!=expected_sha256):
        raise ValueError("Existing file requires its current expected_sha256 from read_workspace_text.")
    if not p.exists() and expected_sha256:
        raise ValueError("Expected an existing file but none exists.")
    old=p.read_text(encoding="utf-8-sig") if p.exists() else ""
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text,encoding="utf-8")
    return {"path":str(p),"sha256":digest(p),"diff":"".join(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile="before",tofile="after"))[:16000]}
