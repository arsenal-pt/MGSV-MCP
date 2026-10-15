# Contributing to MGSV MCP

The project is under active development and original implementation was AI-written through OpenAI Codex under arsenal-pt's direction. Human expertise is welcome: review assumptions, improve code and tests, explain mistakes and help make the tools dependable.

High-value contributions: native format round-trip fixtures without game assets; source/revision accuracy; missing virtual entity indexing; adapter options/version resolution; Windows/.NET compatibility; path/XML/archive safety; readable errors; portability and performance.

1. Open an issue or fork a focused branch. Describe the problem, expected behavior and relevant versions.
2. Keep source originals immutable and native executables outside the repository. Use tiny authored synthetic fixtures. Never submit game files, saves, caches, credentials or copied third-party implementations.
3. Add a meaningful regression test for behavior changes. Run `python -m pytest -q`; native `verify_*.py` checks are separate and need their own trusted tools.
4. Cite primary upstream source links/commits. Separate documented APIs, source observations, synthetic tests and actual converter/game results.
5. For an adapter, document extensions, argument/options, runtime/sidecars, output locations, timeouts, pinned release/hash, limitations and round-trip evidence. Reference-only/GUI entries must not claim execution support.
6. Submit a pull request with scope, rationale, validation and remaining limits. State AI assistance honestly and credit upstream work. Human-authored contributions will be credited separately.

Contributions should be compatible with GPL-3.0-only for eligible original code. Third-party material needs its own compatible permission and attribution; do not assume the project license relicenses it. You keep authorship of your contribution. Forks and distributed derivatives are governed by applicable GPL terms; sending improvements back here and crediting arsenal-pt/MGSV MCP are appreciated, not additional license restrictions.

## Preserve upstream attribution

When adding or changing an adapter/reference, name the original creator and credited contributors, link the primary project, distinguish fork maintenance from original authorship, and update CREDITS.md plus the attribution index/records. Preserve applicable upstream notices. If an author is unknown, mark the gap explicitly and supply evidence with corrections; do not infer sole authorship from a repository owner.
