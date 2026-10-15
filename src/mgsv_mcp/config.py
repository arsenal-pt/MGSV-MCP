from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Config:
    root: Path = ROOT
    workspace: Path | None = None
    read_roots: list[Path] = field(default_factory=list)
    game_roots: list[Path] = field(default_factory=list)
    tools: dict = field(default_factory=dict)

    def __post_init__(self):
        self.root = self.root.resolve()
        self.workspace = (self.workspace or self.root / "workspace").resolve()
        self.read_roots = [p.resolve() for p in self.read_roots]
        self.game_roots = [p.resolve() for p in self.game_roots]
        if any(self.workspace.is_relative_to(p) or p.is_relative_to(self.workspace)
               for p in self.game_roots):
            raise ValueError("The workbench and live game folders must not overlap.")

    @property
    def data(self):
        return self.root / "data"

    @property
    def db(self):
        return self.data / "wiki.sqlite3"

    @property
    def upstream(self):
        return self.data / "upstream"

    @classmethod
    def load(cls):
        root = Path(os.environ.get("MGSV_MCP_HOME", ROOT)).resolve()
        path = root / "config.local.json"
        values = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
        return cls(root=root,
                   workspace=Path(values["workspace"]) if values.get("workspace") else None,
                   read_roots=[Path(p) for p in values.get("read_roots", [])],
                   game_roots=[Path(p) for p in values.get("game_roots", [])],
                   tools=values.get("tools", {}))

    def readable(self, value: str) -> Path:
        p = Path(value)
        p = (p if p.is_absolute() else self.workspace / p).resolve()
        if not any(p.is_relative_to(root) for root in [self.workspace, *self.read_roots, *self.game_roots]):
            raise ValueError("Input is outside configured read roots. Add its parent to config.local.json.")
        if not p.exists():
            raise ValueError("Input file or directory does not exist.")
        return p

    def writable(self, value: str, *, exists: bool = False) -> Path:
        p = Path(value)
        p = (p if p.is_absolute() else self.workspace / p).resolve(strict=exists)
        if not p.is_relative_to(self.workspace) or p == self.workspace:
            raise ValueError("Output must be a child of the workbench workspace.")
        if any(p.is_relative_to(root) for root in self.game_roots):
            raise ValueError("Writing to a live game folder is not supported.")
        return p
