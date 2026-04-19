"""Tests for the ConTree-backed workspace adapter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


pytest.importorskip("contree_sdk")


class _AwaitableImage:
    """Minimal stand-in for a ContreeImage: its run() returns an awaitable image."""

    def __init__(self, *, stdout: str = "", stderr: str = "", exit_code: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.uuid = "img-1"
        self.tag = None
        self.run_calls: list[dict] = []

    def run(self, *args, **kwargs):
        # Mirror the SDK: run() returns a new awaitable image instance.
        call = {"args": args, "kwargs": kwargs}
        self.run_calls.append(call)
        result = _AwaitableImage(
            stdout=kwargs.get("_stdout", ""),
            stderr=kwargs.get("_stderr", ""),
            exit_code=kwargs.get("_exit_code", 0),
        )
        result.run_calls = self.run_calls

        async def _coro():
            return result

        return _coro()


@pytest.mark.asyncio
async def test_contree_workspace_prepare_uses_tagged_image(tmp_path: Path):
    from cbc.workspace.backends import SandboxMode, StagedLease
    from cbc.workspace.contree_adapter import ContreeWorkspace

    fake_image = _AwaitableImage()
    fake_client = MagicMock()
    fake_client.images.use.return_value = fake_image

    ws = ContreeWorkspace(client=fake_client, task_id="t1")
    lease = await ws.prepare_async(tmp_path)

    fake_client.images.use.assert_called_once_with("cbc/workspace/t1:v1")
    assert isinstance(lease, StagedLease)
    assert lease.backend is ws
    assert ws.mode is SandboxMode.CONTREE

    # prepare_async should stage the base_dir into the image via files= mapping.
    assert len(fake_image.run_calls) == 1
    kwargs = fake_image.run_calls[0]["kwargs"]
    assert kwargs.get("disposable") is False
    assert kwargs.get("files") == {"/work": str(tmp_path)}


def test_contree_workspace_sync_prepare_raises(tmp_path: Path):
    from cbc.workspace.contree_adapter import ContreeWorkspace

    ws = ContreeWorkspace(client=MagicMock(), task_id="t1")
    with pytest.raises(RuntimeError, match="async"):
        ws.prepare(tmp_path)


def test_contree_workspace_tag_format():
    from cbc.workspace.contree_adapter import ContreeWorkspace

    ws = ContreeWorkspace(client=MagicMock(), task_id="my-task-123")
    assert ws.tag() == "cbc/workspace/my-task-123:v1"
