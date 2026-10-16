# Animation references and provenance

Reviewed 15 October 2026. This is an authored navigation note, not a copy of the upstream guide or a native test.

## Find the sources in MCP

- `search("Adding Player Motions")`, then `fetch("resource:choc-adding-player-motions")`.
- `search("BossQuiet2_layers")`, then `fetch("resource:bobdoleowndu-bossquiet2-layers-notes")`.
- `modding_workflow("animations")` provides a bounded checklist in the updated source. An existing connection needs its next normal reconnect to load changed Python workflows; a rebuilt index exposes the references through its existing search/fetch tools immediately.

Existing installations can use `python server.py reindex` to rebuild from their retained wiki and additional-source snapshots. This requires an existing wiki checkout, performs no upstream refresh and retains the snapshots. Fresh clones use the normal documented setup. The two added web references are curated notes and links; refresh never downloads the full guide or description list.

## Keep identity and directory types separate

Store category, tags, virtual GANI directory, container chain, description and attribution/match status separately. A virtual asset directory is not a disk folder or installation destination. Preserve an exact member's hash/path and the containing archive hash, extraction ordinal, tool version and dictionary snapshot. A numerical ordinal can change after repacking.

The guide distinguishes the FPK package load list from the GANI playback list. Its runtime examples use a leading `/Assets/` and `.gani`; preserve extensionless catalogue/hash identifiers in their original field. Groups and hold controls are player-playback features. They do not establish safe transitions, paired contact or ordinary NPC compatibility. IH and unknown321's alternative motions mod have different controls. [Configuration and usage](https://github.com/chocmake/chocmake.github.io/blob/2301912bd8694e5abd81044b0e9b15c811cb5772/guides/mgsv-adding-player-motions/index.html#L924), [order warning](https://github.com/chocmake/chocmake.github.io/blob/2301912bd8694e5abd81044b0e9b15c811cb5772/guides/mgsv-adding-player-motions/index.html#L1738).

The supplied BobDoleOwndU notes identify their own source as:

| Container | Virtual path |
| --- | --- |
| DAT | `chunk2.dat` |
| FPK | `Assets/tpp/pack/mission2/story/s10050/s10050_area.fpk` |
| MTAR | `Assets/tpp/motion/mtar/bossquiet2/BossQuiet2_layers.mtar` |

That chain applies only to that reference. An exact archive/member match is required before using its descriptions for another catalogue. The note supplies no binary hashes. `_layers` in a filename establishes no general base-versus-layer decoding rule. [Source location header](https://github.com/chocmake/chocmake.github.io/blob/2301912bd8694e5abd81044b0e9b15c811cb5772/guides/mgsv-adding-player-motions/files/gani-descriptions/BobDoleOwndU/BossQuiet2_layers.txt#L1).

For troubleshooting, the guide checks loaded packages, exact paths/groups, dictionaries and XML/member consistency. A tool can pack a file while custom paths resolve to alternate hashes; a zero exit status is insufficient. [Troubleshooting](https://github.com/chocmake/chocmake.github.io/blob/2301912bd8694e5abd81044b0e9b15c811cb5772/guides/mgsv-adding-player-motions/index.html#L1458).

## Credits, review scope and reuse

Credit **choc / chocmake** for *Adding Player Motions* and **BobDoleOwndU** for *BossQuiet2_layers* notes, explicitly attributed by the [resource table](https://github.com/chocmake/chocmake.github.io/blob/2301912bd8694e5abd81044b0e9b15c811cb5772/guides/mgsv-adding-player-motions/index.html#L1589). Other linked description lists retain their own named authors, including amars464 and Shigu. **KnochenGott** supplied the separate enemy-animation workbook according to the user; it remains private and is not bundled here.

Pinned source repository commit: `2301912bd8694e5abd81044b0e9b15c811cb5772` (6 June 2026); guide last edited 5 June 2026. Guide blob: `d057a583ed08cddf3bad992318cb6eb3279a054d`; description-note blob: `cc849df018389da78f0d5f76f224eedec174d63e`. Only concise authored summaries and links are included. An applicable redistribution license for the complete guide/notes was not verified; this project's code license does not relicense them. No extraction, game launch, installation or native playback test was performed for this update.
