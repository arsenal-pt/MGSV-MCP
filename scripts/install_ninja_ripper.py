"""Install the reviewed free 1.7.1 portable package without executing its programs."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mgsv_mcp.config import Config
from mgsv_mcp.supplements import save_snapshot

PACKAGE_ID = "ninja-ripper-1.7.1"
SHA256 = "19fb1f20d4f435a35056380bb07f3736467b1f30a0c727fb9c6a754897782d55"
SOURCE = "https://cgig.ru/ninjaripper/"
DOWNLOAD = "https://www.mediafire.com/file/z1w91t5keytvq3r/ninjaripper1.7.1_with_new_script.7z"


def install(archive, seven_zip=None):
    archive = Path(archive).resolve(strict=True)
    if not archive.is_file() or archive.stat().st_size > 16_000_000:
        raise ValueError("Expected the reviewed archive, under 16 MB")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Archive SHA-256 does not match the reviewed publisher release")
    seven_zip = seven_zip or shutil.which("7z") or str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "7-Zip/7z.exe")
    if not Path(seven_zip).is_file():
        raise ValueError("7-Zip is required; pass --seven-zip with its executable path")
    config = Config(root=ROOT)
    destination = (config.data / "tool-bin/NinjaRipper/1.7.1").resolve()
    assert destination.is_relative_to((config.data / "tool-bin").resolve())
    listing = subprocess.run([str(seven_zip), "l", "-slt", str(archive)], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=30, check=True).stdout
    expanded_size = 0
    for block in listing.split("----------", 1)[1].strip().split("\n\n"):
        fields = dict(line.split(" = ", 1) for line in block.splitlines() if " = " in line)
        name = fields.get("Path", "")
        windows_path = PureWindowsPath(name)
        target = (destination / name).resolve()
        if not name or windows_path.drive or windows_path.is_absolute() or not target.is_relative_to(destination):
            raise ValueError("Unsafe archive path")
        if "Symbolic Link" in fields or "Hard Link" in fields or fields.get("Encrypted") == "+":
            raise ValueError("Links and encrypted entries are not supported")
        expanded_size += int(fields.get("Size", "0"))
    if expanded_size > 64_000_000:
        raise ValueError("Archive exceeds extraction limit")
    destination.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(seven_zip), "x", str(archive), "-o" + str(destination), "-y", "-bb0"],
                   capture_output=True, text=True, timeout=60, check=True)
    for relative in ["x64/NinjaRipper.exe", "x86/NinjaRipper.exe", "help_en.txt", "whats_new.txt"]:
        if not (destination / relative).is_file():
            raise ValueError("Required package file is missing: " + relative)
    components = [
        {"name": "Ninja Ripper x64 GUI", "path": "x64/NinjaRipper.exe"},
        {"name": "Ninja Ripper x86 GUI", "path": "x86/NinjaRipper.exe"},
        {"name": "Blender importer (legacy bundled ZIP)", "path": "tools/blender_ninjaripper_importer/blender-import-ninjaripper-master.zip"},
        {"name": "Noesis importer", "path": "tools/noesis_importer/fmt_ninjaripper_rip.py"},
        {"name": "3ds Max importers", "path": "tools/3dmax_maxscript_importer"},
        {"name": "GIMS importer packages", "path": "tools/3dmax_GIMS_importer"},
        {"name": "RIP dump helper (not executed)", "path": "ripdump.exe"},
    ]
    for component in components:
        component["path"] = (destination / component["path"]).relative_to(ROOT).as_posix()
        component["execution_supported"] = False
    record = {"package_id": PACKAGE_ID, "version": "1.7.1", "source_page": SOURCE, "url": DOWNLOAD,
              "sha256": SHA256, "size": archive.stat().st_size, "installation_kind": "portable-gui",
              "install_root": destination.relative_to(ROOT).as_posix(), "components": components,
              "executables": [p.relative_to(ROOT).as_posix() for p in destination.rglob("*.exe")],
              "file_sha256": {p.relative_to(destination).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in destination.rglob("*") if p.is_file()}}
    manifest = config.data / "installed-tools.json"
    records = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
    records = [r for r in records if r.get("package_id") != PACKAGE_ID] + [record]
    temp = manifest.with_suffix(".tmp")
    temp.write_text(json.dumps(records, indent=2), encoding="utf-8")
    temp.replace(manifest)
    docs = []
    for relative, fallback in [("help_en.txt", "cp1252"), ("whats_new.txt", "cp1251"),
                               ("tools/3dmax_maxscript_importer/readme_for_ninja_importerb7_cl69.txt", "cp1252")]:
        data = (destination / relative).read_bytes()
        try:
            body = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            body = data.decode(fallback)
        docs.append({"path": relative, "body": body, "url": DOWNLOAD})
    save_snapshot(config, "ninja-ripper", {"source_id": "ninja-ripper", "package_id": PACKAGE_ID,
        "revision": "sha256:" + SHA256, "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {"version": "1.7.1", "distribution": "free legacy public version", "archive_sha256": SHA256,
                     "provenance": "Author-endorsed CG in Games release link; programs not executed"},
        "documents": docs})
    return {"package_id": PACKAGE_ID, "version": record["version"], "installation_path": str(destination),
            "sha256": SHA256, "files": len(record["file_sha256"]), "cached_documents": len(docs),
            "execution_supported": False, "note": "Portable GUI and bundled importers installed; no program launched or game files modified."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, help="Original publisher-linked 1.7.1 .7z file")
    parser.add_argument("--seven-zip", help="Optional 7z.exe path")
    args = parser.parse_args()
    print(json.dumps(install(args.archive, args.seven_zip), indent=2))
