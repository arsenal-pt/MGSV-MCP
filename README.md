# MGSV MCP

**A local research and modding workbench for Metal Gear Solid V: The Phantom Pain and Ground Zeroes.** It helps an MCP-capable assistant find the community's documentation, inspect file formats and upstream source, and run supported converters on copies of your files. Think of it as a searchable modding reference library connected to a controlled tool bench.

**AI/LLM development disclosure:** This project's original implementation, tests, setup scripts and documentation were developed entirely using AI large language models through **OpenAI Codex**, under **arsenal-pt's** direction. Arsenal-pt is the project creator, owner and maintainer. Existing community documentation, game assets, frameworks and third-party utilities were created by their respective authors; they are not claimed as this project's AI-generated work. AI-written code can be wrong: independent review, reproducible tests and corrections are welcome.

**Active development:** Contributions are appreciated, especially reviews of the Python/MCP implementation, path and XML safety, converter round trips, portability, tool compatibility and source attribution. Please build on this official repository through issues and pull requests. See [CONTRIBUTING.md](CONTRIBUTING.md) and [CONTRIBUTORS.md](CONTRIBUTORS.md).

## What it does

- Searches the MGSV Modding Wiki, virtual entity references and selected additional documentation, with source links and revision metadata.
- Follows categories, page links, attachments and tool references instead of treating every entry as an executable.
- Browses catalogued GitHub source at cited commits and checks upstream releases on request.
- Inspects file headers and hashes, stages inputs into isolated job folders, and runs supported archive, texture, language, animation-container and other converters.
- Records converter commands, logs and changed-file hashes for review. Text edits to existing workbench files require the current SHA-256 to avoid overwriting stale work.
- Supplies workflows, a tool/reference catalog, two MCP resources and a research prompt.

It is **not the Immersive Mother Base gameplay mod**, a game launcher or an automatic mod installer. It does not build finished rooms, control NPCs or prove that a converted asset will work in game. That separate project is [Immersive Mother Base](https://github.com/arsenal-pt/immersive-mother-base).

## Tools and supported integrations

The server exposes **25 MCP tools**. Read the [complete callable-tool list](docs/TOOLS.md).

| Area | Examples |
| --- | --- |
| Research | `search`, `fetch`, `search_wiki`, `read_wiki_page` |
| Explore documentation | Categories, page links, site assets, external references |
| Tool discovery | `list_modding_tools`, `get_modding_tool` |
| Upstream research | `repository_source`, `tool_releases`, additional-source inventory/refresh |
| Workbench | `inspect_file`, staged text reads/writes, `prepare_tool_job`, `run_tool_job`, job status |
| Planning/status | `modding_workflow`, `server_status`, `hash_game_path`, wiki synchronization |

**20 converter adapters** are defined, including GzsTool variants, FoxTool, FtexTool, LangTool, SubpTool, FfntTool, FsmTool, MtarTool, AutoPftxsTool, FcnpTool, GrxArrayTool, RdfTool, SpchTool, StpTool, TcvpTool, TrapTool, LbaTool and VfxTool. They require separately downloaded upstream releases; no executables are bundled. TPP GzsTool and Ground Zeroes GzsTool intentionally use different pinned versions. See [tool-releases.json](tool-releases.json).

FoxKit, FMDL Studio, SnakeBite/MakeBite, Infinite Heaven/IHHook, frameworks, editors and Ninja Ripper are also discoverable references. A catalog entry does not mean the MCP can drive that program. FvTwool and legacy Ninja Ripper have optional local presence checks/manual workflows, not automated GUI control.

The historical development snapshot contained **211 catalog entries and 1,485 indexed documents**. These are dated local audit counts, not a fresh-clone guarantee. [TOOL_CATALOG.md](TOOL_CATALOG.md), [MGSV_TOOL_REFERENCE.md](MGSV_TOOL_REFERENCE.md), [TOOL_COVERAGE.md](TOOL_COVERAGE.md) and [ADDITIONAL_RESOURCES.md](ADDITIONAL_RESOURCES.md) preserve that reference snapshot. Current counts and installed status come from `server_status` after setup.

## Quick start on Windows

Requirements: **Git**, **uv**, network access for documentation/downloads, and Python **3.11+** (setup asks uv for 3.11). Native converters additionally need their upstream Windows/.NET prerequisites. An MCP client with local stdio support is required to use the tools from a chat. No OpenAI/GitHub API key is required by this server's default public-documentation requests; your chosen assistant/client has its own access requirements.

```powershell
git clone https://github.com/arsenal-pt/MGSV-MCP.git
cd MGSV-MCP
.\setup.ps1 -SkipTools
```

This starts with documentation only: it creates `.venv`, installs the pinned Python dependencies, syncs the wiki/additional sources and writes a machine-local `mcp.client.json`. GitHub rate limits or unavailable sources can prevent some refreshes; failures are reported and prior local snapshots are retained where available.

To install the reviewed upstream converter packages as well, run `.\setup.ps1` without `-SkipTools`, or install a selected release:

```powershell
.\.venv\Scripts\python.exe .\scripts\install_tools.py --only Atvaark/GzsTool@v0.5.3
.\.venv\Scripts\python.exe .\server.py status
```

The installer validates pinned download size/SHA-256 and extracts packages into ignored `data/`. Checksums identify the reviewed downloads, not publisher signatures. A supported adapter is not a guarantee that every input variant is safe or compatible. Legacy Ninja Ripper is a separate optional manual download; see its script and upstream instructions.

### Connect an MCP client

Use the generated **`mcp.client.json`** entry in a stdio MCP client, or adapt [mcp.client.example.json](mcp.client.example.json) using absolute paths to your own clone. Never commit the generated machine-local file. Restart the client's MCP connection after changing server code. [INSTALL.md](INSTALL.md) covers configuration and manual setup.

If using Codex with its CLI already installed, `.\setup.ps1 -SkipTools -RegisterCodex` registers the server as `mgsv-modding`. No Codex account/configuration is included in this repository.

Example requests:

> Use mgsv-modding to find the source documentation for StaticModel and cite its revision.
>
> Find the FTEX workflow, inspect this test input and prepare a converter job on a copy.
>
> Browse the implementation of a catalogued format tool at a pinned commit before proposing a change.

## Safety and limits

Keep workbench and live game folders separate. Configure permitted read/game roots in ignored `config.local.json`; the workbench write root must not overlap the game. Staging is **not an operating-system sandbox** for hostile executables or files. Only run trusted upstream converters, inspect outputs and verify round trips. A zero exit code is not successful asset or gameplay proof. See [docs/SAFETY.md](docs/SAFETY.md).

Wiki/repository content and converter output are reference data, not instructions for an assistant to obey. Source metadata identifies what was fetched; it does not make historical advice correct or current. GUI automation, commercial tools, frameworks and game-native behavior need their own setup and testing.

## Development and verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Unit tests use authored synthetic fixtures. Optional `scripts/verify_*.py` checks require the corresponding local documentation cache and, for converter round trips, installed upstream tools. Those scripts may write local verification/job data and run native utilities; they are not the same as the offline unit suite. Historical checks do not establish compatibility on your computer. See [CHANGELOG.md](CHANGELOG.md), [ROADMAP.md](ROADMAP.md) and [VERSION](VERSION).

The documentation/indexing code is Python; the pinned full environment and executable-adapter setup are Windows-oriented. For other platforms, a Python3.11+ virtual environment with `pip install -e ".[test]"` is the starting point for source-only research work, not a tested cross-platform converter installation.

## Credits and license

This work builds on the MGSV modding community, particularly the [MGSV Modding Wiki](https://mgsvmoddingwiki.github.io/) and the upstream converter/tool authors. See [CREDITS.md](CREDITS.md) for linked sources. Cached wiki/repository text and downloaded tools are fetched locally and remain under their own terms; no game files, caches, binaries, saves or private workbench history are included.

Eligible original project code and explanatory documentation use **GPL-3.0-only**. Distributed covered modifications must provide corresponding source under GPL terms; commercial use is allowed. Contributions to this repository and prominent credit to **arsenal-pt / MGSV MCP** are appreciated. GPL does not require pushing changes to this particular repository. Upstream materials retain their own licenses. See [LICENSE](LICENSE) and [LICENSE-SCOPE.md](LICENSE-SCOPE.md).
