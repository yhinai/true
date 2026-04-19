"""ConTree-backed workspace adapter. Opt-in via --sandbox=contree."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cbc.workspace.backends import SandboxMode, StagedLease


@dataclass
class ContreeExecResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False


@dataclass
class ContreeWorkspace:
    """Workspace backend that stages work inside a ConTree image."""

    client: Any
    task_id: str
    version: str = "v1"
    mode: SandboxMode = field(default=SandboxMode.CONTREE, init=False)

    def tag(self) -> str:
        return f"cbc/workspace/{self.task_id}:{self.version}"

    async def prepare_async(self, base_dir: Path) -> StagedLease:
        image = await self.client.images.use(self.tag())
        await image.run(
            shell="true",
            files={"/work": str(base_dir)},
            disposable=False,
        )
        return StagedLease(root=Path("/work"), backend=self)

    def prepare(self, base_dir: Path) -> StagedLease:
        raise RuntimeError(
            "ContreeWorkspace requires the async path; call prepare_async."
        )

    def release(self, lease: StagedLease) -> None:
        return None

    async def execute_async(
        self,
        lease: StagedLease,
        cmd: list[str],
        timeout_seconds: float,
    ) -> ContreeExecResult:
        image = await self.client.images.use(self.tag())
        try:
            result = await image.run(
                shell=" ".join(cmd),
                cwd=str(lease.root),
                timeout=timeout_seconds,
                disposable=True,
            )
        except TimeoutError:
            return ContreeExecResult(
                stdout="", stderr="", returncode=-1, timed_out=True
            )
        return ContreeExecResult(
            stdout=_as_text(getattr(result, "stdout", "")),
            stderr=_as_text(getattr(result, "stderr", "")),
            returncode=int(getattr(result, "exit_code", 0) or 0),
        )


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    read = getattr(value, "read", None)
    if callable(read):
        data = read()
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")
        return str(data)
    return str(value)
