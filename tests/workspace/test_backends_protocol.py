from pathlib import Path

from cbc.workspace.backends import LocalBackend, SandboxMode, WorkspaceBackend


def test_sandbox_mode_values():
    assert SandboxMode.LOCAL.value == "local"
    assert SandboxMode.CONTREE.value == "contree"


def test_local_backend_conforms_to_protocol():
    backend: WorkspaceBackend = LocalBackend()
    assert backend is not None


def test_local_backend_prepare_returns_path(tmp_path: Path):
    backend = LocalBackend()
    lease = backend.prepare(tmp_path)
    assert lease.root.exists()
    assert lease.root != tmp_path  # staged copy, not in-place
    backend.release(lease)
