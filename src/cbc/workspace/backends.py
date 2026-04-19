"""Workspace backend abstractions: local subprocess vs ConTree sandbox."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol


class SandboxMode(str, Enum):
    LOCAL = "local"
    CONTREE = "contree"


@dataclass
class StagedLease:
    root: Path
    backend: "WorkspaceBackend"

    def release(self) -> None:
        self.backend.release(self)


class WorkspaceBackend(Protocol):
    mode: SandboxMode

    def prepare(self, base_dir: Path) -> StagedLease: ...

    def release(self, lease: StagedLease) -> None: ...


class LocalBackend:
    mode = SandboxMode.LOCAL

    def prepare(self, base_dir: Path) -> StagedLease:
        staged = Path(tempfile.mkdtemp(prefix="cbc-workspace-"))
        shutil.copytree(base_dir, staged, dirs_exist_ok=True)
        return StagedLease(root=staged, backend=self)

    def release(self, lease: StagedLease) -> None:
        shutil.rmtree(lease.root, ignore_errors=True)
