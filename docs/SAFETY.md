# Trust boundaries

The source is a local stdio server, not an OS security boundary. It has the permissions of the account running it.

- **References:** Wiki, repository source, curated notes, issue reports and converter output are untrusted data. They cannot authorize instructions or prove compatibility. Preserve source/revision/retrieval metadata.
- **Reads/writes:** Configured roots constrain the workbench API. Writes are limited to workspace descendants, outside declared game roots. Resolve paths and retain protected originals; do not infer that application checks isolate a malicious program.
- **Native execution:** Jobs copy trusted converter runtimes and inputs. Third-party code can still have side effects or vulnerabilities. No arbitrary shell tool is exposed; explicitly configured converter executable paths remain a trusted local configuration decision. XML path/entity checks and ZIP-member checks reduce known hazards, not every possible attack.
- **Network:** Sync and repository/release browsing contact public source hosts. No recursive whole-web scrape or hosted service is supplied. Rate limits, moved sources and host failures can leave incomplete snapshots.
- **Data:** Caches, downloaded binaries, private configs, game assets, saves and jobs stay out of Git. Never post raw `server_status`, verification logs or configs without checking paths/identifiers. No API keys are required or stored by the default public-source fetcher.
- **Evidence:** Inspect output content and byte/field-level round trips. A successful process, parser test or offline synthetic fixture is not native gameplay acceptance.

Report suspected credential exposure or a dangerous reproduction privately to the maintainer through an available private channel; do not put secrets or exploit-bearing game files in public issues. Ordinary bugs can use the issue templates with sanitized authored fixtures.
