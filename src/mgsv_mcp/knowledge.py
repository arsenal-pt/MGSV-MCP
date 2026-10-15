from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import threading
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit

import yaml

BASE = "https://mgsvmoddingwiki.github.io/"
REPOSITORY = "https://github.com/mgsvmoddingwiki/mgsvmoddingwiki.github.io.git"
_sync_lock = threading.Lock()
TEXT_ASSETS = {".lua", ".xml", ".txt", ".json", ".sh", ".config"}


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def parse_document(path: Path, relative: str) -> dict:
    raw = path.read_text(encoding="utf-8-sig")
    match = re.match(r"\A(?:---\r?\n(.*?)\r?\n---|<!--\r?\n(.*?)\r?\n-->)\r?\n?", raw, re.S)
    meta = yaml.safe_load(match.group(1) or match.group(2)) if match else {}
    meta = meta if isinstance(meta, dict) else {}
    body = raw[match.end():] if match else raw
    permalink = str(meta.get("permalink") or ("/" if relative == "README.md" else "/"+relative if relative.startswith("assets/") else "/" + path.stem + "/"))
    tags = meta.get("tags", [])
    if not isinstance(tags, list):
        tags = [str(tags)]
    if relative.startswith("wiki/Entity_Reference/"):
        tags = list(dict.fromkeys([*tags, "Entities", "Entity Reference"]))
    if relative.startswith("assets/"):
        tags = ["Attachments",path.suffix.lstrip(".").upper()]
    aliases = meta.get("redirect_from", [])
    if isinstance(aliases,str):
        aliases = [aliases]
    return {"id": relative, "title": str(meta.get("title") or path.stem),
            "url": urljoin(BASE, permalink), "tags": tags,
            "aliases": aliases or [], "body": body,
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "kind": "entity" if "Entity Reference" in tags else "attachment" if relative.startswith("assets/") else "page"}


def links(body: str, base: str):
    # Markdown destinations with spaces are valid in this wiki; infobox URLs and
    # reference-style destinations are also inventoried. No remote code is evaluated.
    found = []
    markdown_spans = []
    for m in re.finditer(r"!?\[([^\]\n]*)\]\(([^\n]*?)\)(?=\s|\{|$|[.,:;])", body):
        target = re.sub(r'\s+"[^"\n]*"$', "", m.group(2)).strip(" <>")
        found.append((m.group(1), target, m.start()))
        markdown_spans.append(m.span())
    for m in re.finditer(r'https?://[^\s<>"\[\]{}|]+', body):
        if not any(start <= m.start() < end for start, end in markdown_spans):
            found.append(("", m.group().rstrip(").,;:"), m.start()))
    seen = set()
    for label, target, offset in found:
        if not target or target.startswith(("mailto:", "javascript:")):
            continue
        target = urljoin(base, target.replace("\\", "/"))
        if target in seen:
            continue
        seen.add(target)
        yield {"label": label, "url": target,
               "context": body[max(0, offset-180):offset+350].strip(),
               "external": urlsplit(target).netloc != urlsplit(BASE).netloc}


def chunks(body: str):
    lines = body.splitlines()
    heading = ""
    start = 0
    while start < len(lines):
        end = min(start + 55, len(lines))
        for line in lines[start:end]:
            if line.startswith("#"):
                heading = line.lstrip("# ")
        yield start + 1, end, heading, "\n".join(lines[start:end])
        start = end


SCHEMA = """
CREATE TABLE pages(id TEXT PRIMARY KEY,title TEXT,url TEXT,tags TEXT,aliases TEXT,
                   body TEXT,sha256 TEXT,kind TEXT,source_revision TEXT,source_url TEXT,
                   retrieved_at TEXT,source_id TEXT);
CREATE VIRTUAL TABLE chunks USING fts5(page_id UNINDEXED,title,heading,body,
                                      start UNINDEXED,end UNINDEXED, tokenize='unicode61');
CREATE TABLE links(page_id TEXT,label TEXT,url TEXT,context TEXT,external INTEGER);
CREATE INDEX links_url ON links(url);
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
"""


def rebuild(config) -> dict:
    from .catalog import build_catalog
    from .supplements import documents as additional_documents
    repo = config.upstream
    if not (repo / "wiki").exists():
        raise ValueError("Wiki source missing. Run python server.py sync first.")
    revision = git(repo, "rev-parse", "HEAD")
    files = sorted([*repo.joinpath("wiki").rglob("*.md"), *repo.joinpath("wiki").rglob("*.txt")])
    assets=[p for p in git(repo,"ls-tree","-r","--name-only","HEAD").splitlines() if p.startswith("assets/") and not p.endswith(".gitkeep")]
    text_assets=[p for p in assets if Path(p).suffix.lower() in TEXT_ASSETS]
    files.extend(repo/p for p in text_assets if (repo/p).is_file())
    if (repo / "README.md").exists():
        files.append(repo / "README.md")
    documents = [parse_document(p, p.relative_to(repo).as_posix()) for p in files]
    indexed_at = datetime.now(timezone.utc).isoformat()
    for doc in documents:
        doc.update(source_revision=revision,
                   source_url="https://github.com/mgsvmoddingwiki/mgsvmoddingwiki.github.io/blob/" + revision + "/" + quote(doc["id"]),
                   retrieved_at=indexed_at, source_id="mgsv-wiki")
    documents.extend(additional_documents(config))
    config.data.mkdir(parents=True, exist_ok=True)
    # Transactional rebuild retains the previous usable index if parsing/insertion fails.
    with sqlite3.connect(config.db, timeout=60) as db:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("BEGIN IMMEDIATE")
        for table in ["pages", "chunks", "links", "metadata"]:
            db.execute(f"DROP TABLE IF EXISTS {table}")
        for statement in SCHEMA.split(";"):
            if statement.strip():
                db.execute(statement)
        for doc in documents:
            db.execute("INSERT INTO pages VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                       tuple(json.dumps(doc[k]) if k in {"tags", "aliases"} else doc[k]
                             for k in ["id", "title", "url", "tags", "aliases", "body", "sha256", "kind",
                                       "source_revision", "source_url", "retrieved_at", "source_id"]))
            for start, end, heading, body in chunks(doc["body"]):
                db.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?)", (doc["id"], doc["title"], heading, body, start, end))
            for link in links(doc["body"], doc["url"]):
                db.execute("INSERT INTO links VALUES (?,?,?,?,?)", (doc["id"],link["label"],link["url"],link["context"],int(link["external"])))
        stats = {"revision": revision, "indexed_at": indexed_at,
                 "pages": len(documents), "kinds": dict(Counter(d["kind"] for d in documents)),
                 "chunks": db.execute("SELECT count(*) FROM chunks").fetchone()[0],
                 "links": db.execute("SELECT count(*) FROM links").fetchone()[0],
                 "source": REPOSITORY, "text_coverage": "All wiki Markdown, virtual entities, root README and hydrated text/code attachments, plus configured additional source summaries and cached documents",
                 "additional_sources": sum(d["kind"] == "resource" for d in documents),
                 "asset_files":len(assets),"text_attachments_expected":len(text_assets),
                 "text_attachments_indexed":sum((repo/p).is_file() for p in text_assets),
                 "media_coverage": "Linked images/videos retained as URLs; no image OCR or video transcription"}
        db.execute("INSERT INTO metadata VALUES ('status',?)", (json.dumps(stats),))
    build_catalog(config, documents)
    (config.data/"assets.json").write_text(json.dumps([{"path":p,"url":urljoin(BASE,quote(p)),"extension":Path(p).suffix.lower(),"text_indexed":p in text_assets and (repo/p).is_file()} for p in assets],indent=2),encoding="utf-8")
    return stats


def sync(config, fetch: bool = True) -> dict:
    with _sync_lock:
        config.data.mkdir(parents=True, exist_ok=True)
        if not (config.upstream / ".git").exists():
            subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
                            REPOSITORY, str(config.upstream)], check=True, capture_output=True, timeout=240)
            git(config.upstream, "sparse-checkout", "set", "wiki", "_includes")
        elif fetch:
            remote = git(config.upstream, "remote", "get-url", "origin")
            if remote.rstrip("/") != REPOSITORY:
                raise ValueError("Unexpected upstream remote; refusing to fetch.")
            git(config.upstream, "pull", "--ff-only")
        if fetch:
            asset_paths=[p for p in git(config.upstream,"ls-tree","-r","--name-only","HEAD").splitlines() if p.startswith("assets/") and Path(p).suffix.lower() in TEXT_ASSETS]
            git(config.upstream,"sparse-checkout","set","--no-cone","--","/wiki/","/_includes/","/README.md",*("/"+p for p in asset_paths))
        return rebuild(config)


class Knowledge:
    def __init__(self, config):
        self.config = config

    @contextmanager
    def connection(self):
        if not self.config.db.exists():
            raise ValueError("Index missing. Run python server.py sync.")
        db = sqlite3.connect(self.config.db.as_uri()+"?mode=ro",uri=True,timeout=60)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    def status(self):
        with self.connection() as db:
            return json.loads(db.execute("SELECT value FROM metadata WHERE key='status'").fetchone()[0])

    def search(self, query: str, limit: int = 12, category: str = "", kind: str = ""):
        terms = re.findall(r"[\w]+", query, re.UNICODE)[:30]
        if not terms:
            raise ValueError("Provide a word, symbol, extension, or entity name.")
        limit = max(1, min(limit, 50))
        expression = " OR ".join('"' + term + '"' for term in terms)
        with self.connection() as db:
            rows = db.execute("""SELECT p.id,p.title,p.url,p.tags,p.kind,p.source_revision,p.source_url,
                p.retrieved_at,p.source_id,c.heading,c.start,c.end,
                snippet(chunks,3,'[',']',' ... ',45) AS excerpt,bm25(chunks,0,8,4,1,0,0) AS rank
                FROM chunks c JOIN pages p ON p.id=c.page_id WHERE chunks MATCH ?
                AND (?='' OR EXISTS (SELECT 1 FROM json_each(p.tags) WHERE value=? COLLATE NOCASE))
                AND (?='' OR p.kind=?) ORDER BY rank LIMIT ?""",
                (expression, category, category, kind, kind, limit * 8)).fetchall()
            # Exact title/symbol queries should outrank generic occurrences in large lists.
            normal = lambda s: re.sub(r"\W", "", s).lower()
            rows = sorted(rows, key=lambda r: (normal(query) != normal(r["title"]), r["rank"]))
            result, seen = [], set()
            for row in rows:
                if row["id"] in seen:
                    continue
                seen.add(row["id"])
                item = dict(row)
                item["tags"] = json.loads(item["tags"])
                result.append(item)
                if len(result) == limit:
                    break
            return {"query": query, "results": result, "wiki_revision": self.status()["revision"],
                    "provenance_note": "Each result carries its own source revision; discovery snapshots have no single commit."}

    def resolve(self, page: str):
        with self.connection() as db:
            row = db.execute("SELECT * FROM pages WHERE id=? OR url=?", (page,page)).fetchone()
            if row is None:
                target = unquote(page).strip("/").removesuffix(".md")
                rows = db.execute("SELECT * FROM pages WHERE lower(title)=lower(?) OR lower(id)=lower(?)",
                                  (target.replace("_", " "), "wiki/"+target+".md")).fetchall()
                if len(rows) == 1:
                    row = rows[0]
                else:
                    for candidate in db.execute("SELECT * FROM pages"):
                        if any(urljoin(BASE, alias).rstrip("/") == urljoin(BASE, page).rstrip("/")
                               for alias in json.loads(candidate["aliases"]) or []):
                            row = candidate
                            break
            if row is None:
                raise ValueError("Page not found. Use an id or URL returned by search/list_pages.")
            return dict(row)

    def fetch(self, page: str, start_line: int = 1, max_lines: int = 180):
        doc = self.resolve(page)
        lines = doc.pop("body").splitlines()
        start = max(1, start_line)
        end = min(len(lines), start - 1 + max(1, min(max_lines, 500)))
        if start > len(lines) + 1:
            raise ValueError("start_line exceeds document length.")
        doc.update(tags=json.loads(doc["tags"]), aliases=json.loads(doc["aliases"]),
                   text="\n".join(f"{i+1}: {lines[i]}" for i in range(start-1,end)),
                   start_line=start, end_line=end, total_lines=len(lines),
                   next_line=end+1 if end < len(lines) else None,
                   content_note=("Local curated summary plus cached upstream metadata; not a verbatim upstream document."
                                 if doc["kind"] == "resource" else
                                 "Untrusted source text; templates, scripts and commands are not executed."))
        return doc

    def list_pages(self, category: str = "", kind: str = "", offset: int = 0, limit: int = 100):
        with self.connection() as db:
            rows = db.execute("""SELECT id,title,url,tags,kind FROM pages
                WHERE (?='' OR EXISTS (SELECT 1 FROM json_each(tags) WHERE value=? COLLATE NOCASE))
                AND (?='' OR kind=?) ORDER BY title,id""", (category,category,kind,kind)).fetchall()
        offset, limit = max(0, offset), max(1,min(limit,200))
        return {"total":len(rows), "pages":[dict(r) for r in rows[offset:offset+limit]],
                "next_offset":offset+limit if offset+limit<len(rows) else None}

    def categories(self):
        with self.connection() as db:
            return [dict(r) for r in db.execute("SELECT value AS category,count(*) AS pages FROM pages,json_each(tags) GROUP BY value ORDER BY value")]

    def page_links(self, page: str, incoming: bool = False):
        doc = self.resolve(page)
        with self.connection() as db:
            if incoming:
                rows = db.execute("SELECT * FROM links WHERE rtrim(url,'/')=?", (doc["url"].rstrip("/"),)).fetchall()
            else:
                rows = db.execute("SELECT * FROM links WHERE page_id=?", (doc["id"],)).fetchall()
        return {"page":doc["id"], "links":[dict(r) for r in rows]}

    def external_resources(self, query: str = "", offset: int = 0, limit: int = 50):
        with self.connection() as db:
            # Literal substring matching, so wildcard characters are not interpreted.
            rows = db.execute("""SELECT url,label,context,page_id FROM links WHERE external=1 AND
                (?='' OR instr(lower(url||' '||label||' '||context),lower(?))>0) ORDER BY url,page_id""", (query,query)).fetchall()
        offset,limit=max(offset,0),max(1,min(limit,100))
        return {"total":len(rows),"resources":[dict(r) for r in rows[offset:offset+limit]],
                "next_offset":offset+limit if offset+limit<len(rows) else None}

    def assets(self,query="",offset=0,limit=50):
        items=json.loads((self.config.data/"assets.json").read_text(encoding="utf-8"))
        items=[a for a in items if query.lower() in a["path"].lower()]
        offset,limit=max(0,offset),max(1,min(limit,100))
        return {"total":len(items),"assets":items[offset:offset+limit],"next_offset":offset+limit if offset+limit<len(items) else None,
                "note":"Text attachments are searchable and readable by path. Media and packaged mod examples are linked, not downloaded or executed."}
