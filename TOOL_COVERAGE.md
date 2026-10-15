> Historical development snapshot (October 2026). Installed/downloaded and cache counts below describe that local audit, not a fresh clone. This repository includes no downloaded binaries or cached upstream content. Run `server_status` after your own setup for current state.

# MGSV MCP tool coverage — October 10, 2026

The local server update is version **0.3.1**: **20 installed executable adapters**, **211 catalog entries**, **30 additional sources** and **1,485 indexed documents**. There are 20 installed packages: 19 pinned GitHub release packages plus the separately pinned free Ninja Ripper 1.7.1 archive. Some contain multiple CLI tools; FvTwool and Ninja Ripper are GUI applications. Documentation availability does not imply that an application is installed or callable.

The audit retained the wiki at commit `2326cdf753a6fcfefb1867dd66ed97a078d4d114`. Cached repository documents and author wikis carry their own commits in MCP search/fetch results and [ADDITIONAL_RESOURCES.md](ADDITIONAL_RESOURCES.md). Public web references have a review date and explicit coverage notes rather than an invented source revision. Publisher READMEs, source code and issue reports were inspected; issue reports are labeled as reports, not verified compatibility findings.

## Requested tools

| Tool | Actual MCP integration | Important distinction |
|---|---|---|
| [FoxTool](https://mgsvmoddingwiki.github.io/FoxTool/) | Installed `foxtool` converter, wiki docs, source/release access | Runs on staged files. |
| [GzsTool](https://mgsvmoddingwiki.github.io/GzsTool/) | Installed `gzstool` v0.5.3 for TPP; `gzstool-bob` fork; newly installed `gzstool-gz` v0.2 for Ground Zeroes | G0S and TPP DAT use separate pinned executables. Wiki warns about v0.6 repacking. |
| [MGSV QAR Tool](https://github.com/Atvaark/TPP.FileFormats) | Explicit historical reference and links to callable GzsTool alternatives | Sergeanur's original binary is not installed; GzsTool is a different implementation. |
| [File Monolith](https://github.com/morbidslinky/FileMonolith) | Cached author README, source/release browsing, all seven suite components catalogued | Windows .NET 8 WinForms suite; no installed/automated GUI claimed. |
| [FMDL Studio V2](https://github.com/BobDoleOwndU/FMDL-Studio-v2) | Cached README and all eight author wiki pages, source/release browsing | Unity importer/exporter; Blender interchange needs compatible host/importer versions. No Unity automation adapter. |
| [FvTwool](https://github.com/BobDoleOwndU/FvTwool) | v1.5.1 GUI executable downloaded; status now reports its presence; author README/source access | `execution_supported=false`; GUI behavior is not automated or tested. |
| [MtarTool](https://github.com/BobDoleOwndU/MtarTool) | Installed `mtartool` archive converter | Animation/rig authoring is a separate operation; the Blender MTAR add-on is now also indexed. |
| [FsmTool](https://github.com/BobDoleOwndU/FsmTool) | Installed `fsmtool`, wiki and source access | FSM cutscene DEMO/SND chunks, including WEM-related workflow; not a general animation editor. |
| [FtexTool](https://github.com/Atvaark/FtexTool) | Installed `ftextool` | DDS/FTEX conversion; matching FTEXS sidecars are staged. |
| [AutoPftxsTool](https://github.com/BobDoleOwndU/AutoPftxsTool) | Installed `autopftxstool` v0.2 | Publisher marks this release prerelease. |
| [Ninja Ripper 1.7.1](https://cgig.ru/ninjaripper/) | **Free legacy package installed**: x64/x86 GUIs and bundled importers; three bundled text documents indexed | GUI capture and the bundled helper are not automated or tested. Uses legacy `.rip`/`.dds`; do not apply paid 2.x `.nr` instructions or capability claims. |

File Monolith's seven components are Archive Unpacker, Mass Texture Converter, File Proliferator, Filename Updater, Archive Transferrer, Texture Aggregator and Regex File Copier. Their documentation is included; they are not seven executable MCP adapters. An Archive Transferrer path issue is linked as an unverified upstream report.

### Free Ninja Ripper 1.7.1

The current [publisher FAQ](https://www.ninjaripper.com/faq) identifies 1.7.1 as the public alternative to paid Ninja Ripper 2. The original author support thread links the [CG in Games release page](https://cgig.ru/ninjaripper/), whose download points to this [publisher-selected archive](https://www.mediafire.com/file/z1w91t5keytvq3r/ninjaripper1.7.1_with_new_script.7z). That exact archive was downloaded and installed; an independent mirror was not used.

- Local folder: `data/tool-bin/NinjaRipper/1.7.1/`; GUI paths: `x64/NinjaRipper.exe` and `x86/NinjaRipper.exe`.
- Includes Blender/Noesis/3ds Max and GIMS importers, plus `ripdump.exe`; all remain manual components, not converter adapters.
- Archive SHA-256: `19fb1f20d4f435a35056380bb07f3736467b1f30a0c727fb9c6a754897782d55`. The installed record also contains each file's checksum.
- The English help, changelog and Max importer notes are searchable as `package-document`, with `source_revision=sha256:<archive-hash>`. Package identity comes from the publisher page, changelog and pinned archive; both GUI PE version fields are `0.0.0.0`.
- The legacy help describes captured vertex blend attributes; this is not a guarantee of complete skeletons, animation or a reversible MGSV model workflow. Current Blender support for the bundled legacy importer remains unverified.
- Ask for `get_modding_tool` with `Ninja Ripper 1.7.1`, or `modding_workflow` with topic `ninja-ripper`. Version 2.x licensing is not a requirement for this selected free release.
- Installation and MCP visibility are tested. No capture, helper execution, wrapper deployment or game modification was performed. The optional helper usage check was rejected by automatic approval review as unapproved third-party execution.

## Remaining supplied links

| Supplied link | What it contains | Coverage |
|---|---|---|
| [Nexus 358](https://www.nexusmods.com/metalgearsolidvtpp/mods/358) | MGSV Batch Unpacker | Reviewed wrapper reference; its underlying archive/XML/texture converters are callable individually. Original batch wrapper not installed. |
| [Nexus 739](https://www.nexusmods.com/metalgearsolidvtpp/mods/739) | File Monolith | Retained alongside the author's cached GitHub documentation. |
| [Nexus 139](https://www.nexusmods.com/metalgearsolidvtpp/mods/139) | MGSV Lua Modding Tutorial | Historical tutorial reference; not an executable tool. |
| [Nexus 571](https://www.nexusmods.com/metalgearsolidvtpp/mods/571) | SideOp Companion | Existing SOC repository and eight author wiki guides remain indexed; GUI not automated. |
| [Steam 547190360](https://steamcommunity.com/sharedfiles/filedetails/?id=547190360) | MGSV model-file locations guide | Historical/incomplete reference; no installer. |
| [Steam 883495538](https://steamcommunity.com/sharedfiles/filedetails/?id=883495538) | Source Filmmaker collection of MGSV models/props | Asset-collection reference; not an MGSV conversion tool. |
| [Nexus modder resources](https://www.nexusmods.com/games/metalgearsolidvtpp/mods?categoryName=Modders+Resources+and+Tutorials) and [page 2](https://www.nexusmods.com/games/metalgearsolidvtpp/mods?categoryName=Modders+Resources+and+Tutorials&page=2) | Category discovery pages | Both links retained. The listing was not fully retrievable, so there is no claim that every item in the category was indexed. No bulk Nexus scrape or download. |

## Added author sources worth using

These are selected for concrete MGSV workflows and author/community documentation, not a claim of a measured popularity ranking. They provide cached documentation and upstream source browsing; host applications, DLL deployment and package installation are not automated.

| Project | Use | Requirements/limits captured |
|---|---|---|
| [SnakeBite / MakeBite](https://github.com/TinManTex/SnakeBite) | Mod management and `.mgsv` packaging | README and developer notes; game/version compatibility must be checked. MakeBite has an upstream CLI entry point, but no verified MCP packaging adapter yet. |
| [Infinite Heaven](https://github.com/TinManTex/InfiniteHeaven) | Lua and custom mission development | Framework source/docs; not installed into a game by this update. |
| [IHHook](https://github.com/TinManTex/IHHook) | Native hooks, Lua extensions and developer logging | README and developer notes; executable-version-sensitive. |
| [Zeta](https://github.com/ZipfsLaw/Zeta) | Custom equipment/content framework | Depends on a compatible Infinite Heaven setup. |
| [Fox Engine MTAR Tools for Blender](https://github.com/mctrollin/fox_engine_mtar_tools_blender) | GANI1/GANI2 animation import/export and custom rig mapping | Author specifies Blender 4.4+ support; some tracks unsupported and repeated import/export can lose information. |
| [MGSV Normal Map Channels Converter](https://github.com/chocmake/MGSV-Normal-Map-Channels-Converter) | Convert normal-map channel layouts | ImageMagick 7+; documented script, not a shell execution adapter. |
| [MGSV lookup strings](https://github.com/TinManTex/mgsv-lookup-strings) | Hash/filename recovery and dictionary development | Source updates do not silently replace converter dictionaries. |
| [wwiser](https://github.com/bnnm/wwiser) | Wwise BNK event/structure inspection | README and detailed manual; cannot modify soundbanks. |

FoxKit, FoxKit-3, SOC, the supplied emulators, NucleusGameFixes, author profiles, MGSV topic discovery and the existing format converters remain included. [TOOL_CATALOG.md](TOOL_CATALOG.md) lists every current catalog entry.

## Verification and use

- `get_modding_tool` accepts catalog IDs and curated aliases, and returns execution support, installation evidence, requirements and limits.
- `server_status` in v0.3.0 includes the running version and each adapter's resolved executable path.
- GitHub documentation refreshes preserve source commits and cached failures. Web-only notes retain their actual review date and are not silently re-scraped.
- Synthetic G0S test: original payload/XML → archive → recovered payload/XML → byte-identical archive. Original inputs were unchanged. The fixture lacks the optional per-entry key header; full game archives and in-game behavior remain unverified.
- Unit tests cover distinct GzsTool versions, GUI presence versus execution, web-reference freshness, source provenance, indexing and workbench file boundaries.
- Evidence: `data/tool-audit-verification.json` (private local audit output; not bundled), `data/additional-sources-verification.json` (private local audit output; not bundled), `data/verification.json` (private local audit output; not bundled).

Restart the MCP client connection to load the updated server code. The existing process continues using its previously loaded implementation; searches read the expanded on-disk index, but the portable-package installation status and Ninja Ripper workflow require version 0.3.1.

Example requests after reconnecting:

> Use mgsv-modding to show server_status and get_modding_tool for Ground Zeroes archive tool.

> Use mgsv-modding to compare FMDL Studio V2, FoxKit-3 and Blender MTAR Tools for a custom character animation workflow. Cite the cached source revisions and identify version requirements.
