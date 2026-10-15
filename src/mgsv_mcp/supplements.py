"""Durable extra sources with bounded, explicit refreshes and per-source provenance."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit

from . import remote

API = "https://api.github.com"
REPO_PATTERN = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"


def sources(config):
    path = config.root / "additional-resources.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported additional-resources schema.")
    # Optional extension keeps older running servers able to read the base manifest
    # until their next restart. They continue serving already-indexed web notes.
    items = data["sources"] + data.get("web_references", [])
    seen = set()
    for item in items:
        if item["id"] in seen:
            raise ValueError("Duplicate additional source ID: " + item["id"])
        seen.add(item["id"])
        kind = item["kind"]
        if kind in {"repository", "github-wiki"}:
            if not re.fullmatch(REPO_PATTERN, item["repository"]):
                raise ValueError("Use a GitHub owner/repository name.")
        elif kind in {"github-profile", "github-topic"}:
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", item.get("owner", item.get("topic", ""))):
                raise ValueError("Invalid GitHub owner or topic.")
        elif kind == "web-reference":
            url = urlsplit(item["url"])
            if url.scheme != "https" or not url.netloc:
                raise ValueError("Web references require an HTTPS source URL.")
            if not item.get("reviewed_at") or not item.get("coverage_note"):
                raise ValueError("Web references need a review date and explicit coverage note.")
        else:
            raise ValueError("Unknown source kind: " + kind)
        for path in item.get("documents", []):
            if PurePosixPath(path).is_absolute() or ".." in path.split("/") or "\\" in path:
                raise ValueError("Additional documents must be repository-relative paths.")
    return items


def cache_path(config, source_id):
    return config.data / "additional-sources" / (hashlib.sha256(source_id.encode()).hexdigest() + ".json")


def cached(config, source_id):
    path = cache_path(config, source_id)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_snapshot(config, source_id, snapshot):
    path = cache_path(config, source_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix("." + uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def api(path):
    return json.loads(remote.request(API + path))


def repo_metadata(item):
    return {k: item.get(k) for k in ["full_name", "description", "html_url", "archived", "fork", "default_branch", "pushed_at", "language"]}


def repository_snapshot(item):
    repo = item["repository"]
    meta = api("/repos/" + repo)
    revision = api("/repos/" + repo + "/commits/" + quote(meta["default_branch"], safe=""))["sha"]
    paths = list(item.get("documents", []))
    readme_found = False
    try:
        readme = api("/repos/" + repo + "/readme?ref=" + revision)
        paths.insert(0, readme["path"])
        readme_found = True
    except HTTPError as exc:
        if exc.code != 404:
            raise
    documents = []
    for path in dict.fromkeys(paths):
        body = remote.request("https://raw.githubusercontent.com/" + repo + "/" + revision + "/" + quote(path, safe="/")).decode("utf-8-sig")
        if "\x00" in body:
            raise ValueError("Additional documentation must be text: " + path)
        documents.append({"path": path, "body": body,
                          "url": "https://github.com/" + repo + "/blob/" + revision + "/" + quote(path, safe="/")})
    issues = []
    if item.get("review_issues") and meta.get("has_issues"):
        issues = [{"title": i["title"], "url": i["html_url"]}
                  for i in api("/repos/" + repo + "/issues?state=open&per_page=5") if "pull_request" not in i]
    return {"metadata": repo_metadata(meta), "revision": revision, "documents": documents,
            "readme_found": readme_found, "issues": issues}


def discovery_snapshot(item):
    found = []
    total = None
    incomplete = False
    # Profiles cap at 500 repos; topic search caps at GitHub's 1,000 results.
    cap = 5 if item["kind"] == "github-profile" else 10
    truncated = False
    for page in range(1, cap + 1):
        if item["kind"] == "github-profile":
            batch = api(f"/users/{item['owner']}/repos?per_page=100&page={page}&sort=full_name")
        else:
            response = api(f"/search/repositories?q=topic%3A{item['topic']}&per_page=100&page={page}&sort=stars")
            batch = response["items"]
            total = response["total_count"]
            incomplete = incomplete or response.get("incomplete_results", False)
        found.extend(batch)
        if len(batch) < 100 or (total is not None and len(found) >= total):
            break
        truncated = page == cap
    # Discovery is descriptive; it never installs or executes the listed projects.
    pattern = item.get("include_pattern", "")
    selected = [r for r in found if not pattern or re.search(pattern, r["full_name"] + " " + (r.get("description") or ""), re.I)]
    unique = {r["full_name"].lower(): repo_metadata(r) for r in selected}
    return {"repositories": sorted(unique.values(), key=lambda r: r["full_name"].lower()),
            "observed_count": len(found), "reported_total": total,
            "truncated": truncated, "incomplete_results": incomplete,
            "filter": pattern or None}


def wiki_snapshot(config, item):
    # A bare clone avoids checkout filters/hooks and only text blobs are indexed.
    repo = item["repository"]
    destination = config.data / "source-wikis" / (hashlib.sha256(repo.encode()).hexdigest() + ".git")
    url = "https://github.com/" + repo + ".wiki.git"
    destination.parent.mkdir(parents=True, exist_ok=True)
    def git(*args):
        result = subprocess.run(["git", "-c", "core.hooksPath=", "-C", str(destination), *args],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()
    if not destination.exists():
        result = subprocess.run(["git", "-c", "core.hooksPath=", "clone", "--bare", "--depth", "1", url, str(destination)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        revision = git("rev-parse", "HEAD")
    else:
        if git("remote", "get-url", "origin") != url:
            raise ValueError("Unexpected additional wiki remote.")
        git("fetch", "--depth", "1", "origin", "HEAD")
        revision = git("rev-parse", "FETCH_HEAD")
    documents = []
    for path in git("-c", "core.quotePath=false", "ls-tree", "-r", "--name-only", revision).splitlines():
        if not path.endswith(".md"):
            continue
        size = int(git("cat-file", "-s", revision + ":" + path))
        if size > 2_000_000:
            raise ValueError("Wiki document exceeds 2 MB: " + path)
        documents.append({"path": path, "body": git("show", revision + ":" + path),
                          "url": item["url"] + "/" + quote(path.removesuffix(".md"), safe="") + "/" + revision})
    return {"revision": revision, "documents": documents}


def refresh(config, source_id=""):
    from .knowledge import _sync_lock, rebuild
    items = sources(config)
    if source_id:
        items = [s for s in items if s["id"].lower() == source_id.lower()]
        if not items:
            raise ValueError("Unknown source ID; use list_additional_sources.")
    with _sync_lock:
        results = []
        for item in items:
            if item["kind"] == "web-reference":
                results.append({"id": item["id"], "status": "reference-only",
                                "reviewed_at": item["reviewed_at"], "note": item["coverage_note"]})
                continue
            try:
                if item["kind"] == "repository":
                    snapshot = repository_snapshot(item)
                elif item["kind"] == "github-wiki":
                    snapshot = wiki_snapshot(config, item)
                else:
                    snapshot = discovery_snapshot(item)
                snapshot.update(source_id=item["id"], retrieved_at=datetime.now(timezone.utc).isoformat())
                save_snapshot(config, item["id"], snapshot)
                results.append({"id": item["id"], "status": "updated", "documents": len(snapshot.get("documents", [])),
                                "repositories": len(snapshot.get("repositories", []))})
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                results.append({"id": item["id"], "status": "error", "error": str(exc),
                                "previous_snapshot_retained": cache_path(config, item["id"]).exists()})
        return {"sources": results, "index": rebuild(config),
                "note": "Failures retain the last successful snapshot. Web references contain reviewed notes and links, are not scraped on refresh, and retain their actual review date. Discovery lists are not exhaustive coverage of all MGSV projects."}


def inventory(config):
    result = []
    for item in sources(config):
        snapshot = cached(config, item["id"])
        result.append(item | {"cached": bool(snapshot), "retrieved_at": snapshot.get("retrieved_at"),
                              "coverage": "curated-reference" if item["kind"] == "web-reference" else "cached-upstream" if snapshot else "pending",
                              "revision": snapshot.get("revision"), "metadata": snapshot.get("metadata"),
                              "cached_documents": len(snapshot.get("documents", [])),
                              "discovered_repositories": len(snapshot.get("repositories", [])),
                              "truncated": snapshot.get("truncated", False),
                              "incomplete_results": snapshot.get("incomplete_results", False)})
    return result


def documents(config):
    result = []
    for item in sources(config):
        snapshot = cached(config, item["id"])
        revision = snapshot.get("revision")
        retrieved = snapshot.get("retrieved_at")
        meta = snapshot.get("metadata", {})
        body = f"# {item['name']}\n\n{item['summary']}\n\nSource: {item['url']}\n"
        body += f"\nSource kind: {item['kind']}\nOrigin: {item.get('origin', 'local manifest')}\n"
        if item["kind"] == "web-reference":
            body += f"Reviewed: {item['reviewed_at']}\nCoverage: {item['coverage_note']}\n"
        if snapshot:
            body += f"Retrieved: {retrieved}\nRevision: {revision or 'discovery snapshot; no single commit'}\n"
        if meta:
            body += "\nRepository metadata:\n" + json.dumps(meta, indent=2, ensure_ascii=False) + "\n"
        for path in item.get("entry_points", []):
            url = f"https://github.com/{item['repository']}/tree/{revision or 'HEAD'}/{quote(path, safe='/')}"
            body += f"\nEntry point: [{path}]({url})\n"
        for url in item.get("related", []):
            body += f"\nRelated: {url}\n"
        if snapshot.get("issues"):
            body += "\n## Recent open issue reports\nIssue titles are user reports, not verified compatibility findings; read the linked discussion.\n"
            for issue in snapshot["issues"]:
                body += f"\n- [{issue['title']}]({issue['url']})\n"
        if "repositories" in snapshot:
            body += f"\n## Discovered repositories\nObserved: {snapshot['observed_count']}; selected: {len(snapshot['repositories'])}; truncated: {snapshot['truncated']}; incomplete: {snapshot['incomplete_results']}\n"
            body += "Profile relevance filter: " + str(snapshot.get("filter") or "none") + "\n"
            for repo in snapshot["repositories"]:
                body += f"\n- [{repo['full_name']}]({repo['html_url']}): {repo['description'] or '(no description)'}; archived={repo['archived']}; fork={repo['fork']}\n"
        summary_url = (f"https://github.com/{item['repository']}/tree/{revision}" if item["kind"] == "repository" and revision else item["url"])
        def document(doc_id, title, body, url, kind):
            return {"id": doc_id, "title": title, "body": body, "url": url,
                    "tags": ["Additional Resources", *item["tags"]], "aliases": [], "kind": kind,
                    "sha256": hashlib.sha256(body.encode()).hexdigest(), "source_revision": revision,
                    "source_url": url, "retrieved_at": retrieved, "source_id": item["id"]}
        summary = document("resource:" + item["id"], item["name"], body, item["url"], "resource")
        summary["source_url"] = summary_url
        result.append(summary)
        for doc in snapshot.get("documents", []):
            result.append(document("source:" + item["id"] + "/" + doc["path"],
                                   item["name"] + " / " + doc["path"], doc["body"], doc["url"],
                                   "package-document" if snapshot.get("package_id") else "repository-document"))
    return result
