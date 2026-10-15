# MCP tools

This list is generated from the public server source. There are **25 MCP tools**, two resources (`mgsv://status`, `mgsv://categories`) and the `research_mod` prompt. Catalog entries are separate from callable tools.

| Tool | Purpose |
| --- | --- |
| `server_status` | Inspect wiki coverage, source commit, installed converter versions and workspace. |
| `search` | Search wiki, entities, supplied resource notes and cached repository documentation, with per-result source citations. |
| `fetch` | Read the first 180 source lines of any indexed document by search result ID or URL. Follow next_line using read_wiki_page. |
| `search_wiki` | Search with optional category and kind (page/entity/attachment/resource/repository-document/package-document). Symbols and extensions work as queries. |
| `read_wiki_page` | Read any indexed document with line numbers and its own provenance; paginate until next_line is null. |
| `list_wiki_pages` | Browse the complete corpus, including Jekyll-generated category membership and virtual entity pages. |
| `wiki_categories` | List every wiki category and indexed document count. |
| `wiki_links` | Return links from a page, or pages linking to it, to follow dependencies and related concepts. |
| `external_resources` | Find every external reference linked by the wiki, including tools without dedicated pages, downloads, videos and research. |
| `wiki_assets` | Browse all site images, videos, example downloads and text/code attachments with source URLs. Use read_wiki_page for indexed text attachments. |
| `list_modding_tools` | Browse converters, editors, frameworks, File Monolith/MakeBite components and linked repositories. Entries report integration level. |
| `get_modding_tool` | Get a tool by catalog ID or unique alias, including capabilities, requirements, limitations, execution support and installation evidence. |
| `tool_releases` | Read official GitHub release notes/assets for a catalogued repository. Does not download or install anything. |
| `repository_source` | Browse or read any catalogued GitHub repository for developing new tools/code updates. Resolves ref to a cited commit; no execution. |
| `list_additional_sources` | List supplied repositories, author profiles, topic discovery and linked documentation, with cached coverage, revisions and freshness. |
| `sync_additional_sources` | Refresh one or all configured GitHub sources and rebuild search/catalog. Retains prior snapshots on failures. Curated web references are preserved with their actual review date and are not scraped. Never installs or runs projects. |
| `modding_workflow` | Get a sourced workflow for lua, textures, models, maps, audio, localization, native-code, tool-development or packaging. Empty topic lists choices. |
| `sync_wiki` | Fetch the official wiki and rebuild documentation/search/catalog, preserving configured additional sources and their cached documents. Existing index survives a failed rebuild. |
| `inspect_file` | Read header bytes, size, SHA-256 and candidate converters for a file in configured read roots or workspace. |
| `prepare_tool_job` | Copy inputs into a fresh job and preview a verified converter command. XML repacking requires input_root with all sidecars. |
| `run_tool_job` | Run a prepared converter once; return exit status, logs and changed-file hashes. May rewrite staged files. Outputs need round-trip/in-game validation. |
| `tool_job_status` | Read a converter job's manifest, outputs and log tails. |
| `hash_game_path` | Calculate filename, extension, with_extension or legacy hash using Bob's GzsTool implementation. |
| `read_workspace_text` | Read local Lua/XML/code/documentation text and its SHA-256 for a later checked edit. |
| `write_workspace_text` | Create/edit source or manifests inside the workbench. Existing files require the current SHA-256. Returns a reviewable diff. |

See [workbench safety](SAFETY.md), the [historical converter/reference guide](../MGSV_TOOL_REFERENCE.md), and the [full catalog snapshot](../TOOL_CATALOG.md). Use `get_modding_tool` for installed status, requirements and supported options.
