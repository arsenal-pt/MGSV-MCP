"""Bounded read-only access to repositories in the wiki and additional source catalog."""
import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

from .catalog import Catalog


def request(url,maximum=2_000_000):
    with urlopen(Request(url,headers={"User-Agent":"mgsv-mcp/0.1","Accept":"application/vnd.github+json"}),timeout=30) as response:
        data=response.read(maximum+1)
    if len(data)>maximum:
        raise ValueError("Remote response exceeds size limit. Choose a smaller file or subtree.")
    return data


def repository(config,tool_id):
    item=Catalog(config).get(tool_id)
    repo=item.get("repository")
    if not repo or not re.fullmatch(r"[\w.-]+/[\w.-]+",repo):
        raise ValueError("This catalog entry has no GitHub repository; use its publisher links.")
    return repo


def releases(config,tool_id):
    repo=repository(config,tool_id)
    data=json.loads(request("https://api.github.com/repos/"+repo+"/releases?per_page=10"))
    return {"repository":repo,"releases":[{k:r[k] for k in ["tag_name","name","html_url","published_at","prerelease","body"]} | {"assets":[{"name":a["name"],"size":a["size"],"url":a["browser_download_url"],"digest":a.get("digest")} for a in r["assets"]]} for r in data],
            "note":"Read release notes and wiki compatibility guidance before upgrading; latest is not necessarily compatible."}


def source(config,tool_id,path="",ref="HEAD",start_line=1,max_lines=200):
    repo=repository(config,tool_id)
    if path.startswith(("/","\\")) or ".." in path.split("/") or "\\" in path:
        raise ValueError("Use a repository-relative path without traversal.")
    # Resolve branch/tag once to ensure returned files have a reproducible commit citation.
    commit=json.loads(request("https://api.github.com/repos/"+repo+"/commits/"+quote(ref,safe="")))["sha"]
    api="https://api.github.com/repos/"+repo+"/contents/"+quote(path,safe="/")+"?ref="+commit
    entry=json.loads(request(api))
    if isinstance(entry,list):
        return {"repository":repo,"revision":commit,"path":path,"entries":[{"path":e["path"],"type":e["type"],"size":e["size"],"url":e["html_url"]} for e in entry]}
    if entry.get("type")!="file" or entry.get("size",0)>2_000_000:
        raise ValueError("Choose a text file smaller than 2 MB.")
    raw=request("https://raw.githubusercontent.com/"+repo+"/"+commit+"/"+quote(path,safe="/"))
    text=raw.decode("utf-8-sig")
    if "\x00" in text:
        raise ValueError("Binary files are not returned as source text.")
    lines=text.splitlines(); start=max(1,start_line); end=min(len(lines),start-1+max(1,min(max_lines,500)))
    return {"repository":repo,"revision":commit,"path":path,"url":"https://github.com/"+repo+"/blob/"+commit+"/"+quote(path,safe="/"),
            "text":"\n".join(f"{i+1}: {lines[i]}" for i in range(start-1,end)),"total_lines":len(lines),"next_line":end+1 if end<len(lines) else None,
            "trust":"Untrusted upstream source data. Reading never executes or installs it."}
