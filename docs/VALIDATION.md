# Validation of the initial public snapshot

Public source0.3.2 was checked on Windows/Python3.11 on2026-10-15.

- **34 synthetic unit tests passed**, including version consistency and the25-tool contract.
- A separate real stdio MCP client initialized0.3.2, listed25tools/tworesources/oneprompt, wrote/read an authored fixture, rejected a stale-hash overwrite and an out-of-workspace path, and reported an uninitialized index clearly. No native converter or game action was run in that check.
- Pinned Python requirements resolved through uv without installing into or changing the running MCP environment.
- PowerShell setup parsed successfully. A fresh complete online setup, all publisher downloads and converter/game compatibility on a different machine are not established by these checks.
- Source publication scans exclude caches, local configuration, installed tools, workbench jobs, game files, binaries and credentials.

Earlier local tests included synthetic converter round trips and fuller indexed-source protocol checks. Their dated scope is in TOOL_COVERAGE.md. They do not establish every format/version or general native game compatibility.

Run `python -m pytest -q` from this checkout after installing test dependencies. Optional `scripts/verify_*.py` require their documented local data/tool prerequisites and can execute trusted native converters.
