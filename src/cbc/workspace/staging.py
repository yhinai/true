"""Workspace staging with pluggable sandbox backend."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from cbc.workspace.backends import SandboxMode, StagedLease


@dataclass
class WorkspaceLease:
    root: Path
    path: Path
    sandbox: SandboxMode = SandboxMode.LOCAL
    _staged: StagedLease | None = field(default=None, repr=False)

    def cleanup(self) -> None:
        if self._staged is not None:
            self._staged.release()
            return
        shutil.rmtree(self.root, ignore_errors=True)


def create_workspace_lease(
    source: Path,
    *,
    sandbox: SandboxMode = SandboxMode.LOCAL,
) -> WorkspaceLease:
    if sandbox is SandboxMode.LOCAL:
        temp_dir = Path(tempfile.mkdtemp(prefix="cbc-workspace-"))
        destination = temp_dir / source.name
        shutil.copytree(source, destination)
        return WorkspaceLease(root=temp_dir, path=destination, sandbox=sandbox)
    raise NotImplementedError(
        f"Sandbox mode {sandbox} requires async prepare; use create_workspace_lease_async."
    )


async def create_workspace_lease_async(
    source: Path,
    *,
    sandbox: SandboxMode = SandboxMode.LOCAL,
    task_id: str | None = None,
) -> WorkspaceLease:
    if sandbox is SandboxMode.LOCAL:
        return create_workspace_lease(source, sandbox=sandbox)
    if sandbox is SandboxMode.CONTREE:
        from cbc.workspace.contree_adapter import ContreeWorkspace
        from contree_sdk import Contree

        assert task_id is not None, "task_id required for ContreeWorkspace"
        ws = ContreeWorkspace(client=Contree(), task_id=task_id)
        staged = await ws.prepare_async(source)
        return WorkspaceLease(
            root=staged.root,
            path=staged.root,
            sandbox=sandbox,
            _staged=staged,
        )
    raise ValueError(f"Unknown sandbox mode: {sandbox}")


def stage_workspace(source: Path) -> Path:
    return create_workspace_lease(source).path
