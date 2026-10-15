"""Install only the reviewed release assets pinned in tool-releases.json."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
from urllib.request import Request,urlopen
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def install(only=""):
    if os.name!="nt":
        raise SystemExit("These upstream executable releases require Windows/.NET. Wiki tools still work on other platforms.")
    recipes=json.loads((ROOT/"tool-releases.json").read_text(encoding="utf-8"))
    if only:
        recipes=[r for r in recipes if (r["repo"]+"@"+r["version"]).lower()==only.lower()]
        if not recipes:
            raise ValueError("Unknown pinned release; use owner/repository@version from tool-releases.json.")
    path=ROOT/"data/installed-tools.json"
    records=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    for recipe in recipes:
        repo=recipe["repo"]
        prefix="https://github.com/"+repo+"/releases/download/"
        if not recipe["url"].startswith(prefix):
            raise ValueError("Expected an official repository release URL.")
        folder=ROOT/"data/tool-bin"/repo.replace("/","__")/recipe["version"]
        print("Installing",repo,recipe["version"],flush=True)
        with urlopen(Request(recipe["url"],headers={"User-Agent":"mgsv-mcp/0.1"}),timeout=60) as response:
            blob=response.read(64*1024*1024+1)
        if len(blob)>64*1024*1024 or hashlib.sha256(blob).hexdigest()!=recipe["sha256"]:
            raise ValueError("Release size/checksum mismatch: "+repo)
        folder.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            if sum(m.file_size for m in archive.infolist())>256*1024*1024:
                raise ValueError("Release exceeds extraction limit.")
            for member in archive.infolist():
                target=(folder/member.filename).resolve()
                if not target.is_relative_to(folder.resolve()) or (member.external_attr>>16)&0o170000==0o120000:
                    raise ValueError("Unsafe archive member.")
            archive.extractall(folder)
        records=[r for r in records if (r.get("repo", "").lower(),r["version"])!=(repo.lower(),recipe["version"])]
        records.append({**recipe,"executables":[p.relative_to(ROOT).as_posix() for p in folder.rglob("*.exe")]})
        temporary=path.with_suffix(".tmp")
        temporary.write_text(json.dumps(records,indent=2),encoding="utf-8")
        temporary.replace(path)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--only",default="",help="Install one pinned owner/repository@version without replacing other versions")
    install(parser.parse_args().only)
