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
    INPLACE = "inplace"


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


class InPlaceBackend:
    """No-copy backend: edits happen directly inside the caller's directory.

    Intended for GitHub Actions / git worktree callers that already have an
    isolated checkout and want CBC to operate on it without staging overhead.
    """

    mode = SandboxMode.INPLACE

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def prepare(self, base_dir: Path) -> StagedLease:
        # base_dir is ignored — the caller-supplied root is the workspace.
        target = self.root
        if not target.exists():
            raise FileNotFoundError(f"InPlaceBackend: {target} does not exist")
        if not target.is_dir():
            raise NotADirectoryError(f"InPlaceBackend: {target} is not a directory")
        # Writability probe.
        try:
            probe = target / ".cbc-inplace-probe"
            probe.touch()
            probe.unlink()
        except OSError as exc:
            raise PermissionError(f"InPlaceBackend: {target} is not writable") from exc
        return StagedLease(root=target, backend=self)

    def release(self, lease: StagedLease) -> None:
        # No-op: generated files stay in place.
        return
