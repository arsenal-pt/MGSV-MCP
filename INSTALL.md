# Installation and client setup

## Windows documentation-only setup

Install Git and uv from their official sources. Clone this repository, change into it, and run `.\setup.ps1 -SkipTools`. Python3.11 is requested through uv. This writes only to the clone's `.venv`, ignored `data/`/`workspace/` and generated client configuration; `-RegisterCodex` additionally changes that client's MCP registration when explicitly selected. Existing running MCP connections are not replaced until restarted.

The full setup without `-SkipTools` downloads the releases pinned in `tool-releases.json`. It does not download game assets or install mods. Each converter has its own upstream runtime requirements. Some reference-only/GUI/framework tools need separate installation and cannot be run through these adapters.

## Client command

The setup generates ignored `mcp.client.json` with the absolute interpreter and `server.py` paths. Use that entry in a local-stdio-capable MCP client. The shipped example contains placeholders and must be adjusted. Keep stdout for MCP traffic; diagnostics belong on stderr. This server does not provide a hosted HTTP endpoint or assistant/model service.

Manual Windows environment alternative:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe server.py sync
.\.venv\Scripts\python.exe server.py sync-resources
```

## Local file configuration

Copy `config.example.json` to ignored `config.local.json` only if you need non-default paths. Example paths are placeholders. `workspace` is the only allowed write tree; `read_roots` add permitted source folders; `game_roots` declare game folders that must not overlap the workbench. Relative tool inputs resolve under the workspace. Do not use your game installation as your workspace. `MGSV_MCP_HOME` can select another configuration/data root; that root needs the associated manifests and index data.

## Converter workflow

1. Inspect the input and keep its original hash.
2. Prepare a job, which copies the input and required runtime into a job directory. XML repacking may require a complete `input_root`; FTEX sidecars are copied automatically.
3. Review/edit staged text. Replacing existing text requires its current hash.
4. Run the converter once, inspect logs and new/changed hashes, and perform an appropriate round trip.
5. Native game tests are a separate user-controlled activity. This MCP provides no live mod installer.

## Troubleshooting and removal

Run `python server.py status` from the configured environment. If the index is missing, run `sync`; for GitHub rate-limit or transient failures, retain the cache and retry a targeted refresh later. `server_status` exposes local paths for debugging, so redact its full response before posting issues. A converter reports unavailable until the matching repository/version is installed.

To remove the server, disconnect/remove its entry from your MCP client, close its server process and remove your clone/virtual environment when no longer needed. Preserve any workbench inputs/outputs you want first. No game rollback is required by installing this source-only research server.
