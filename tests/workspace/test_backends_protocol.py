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


def test_create_workspace_lease_defaults_to_local(tmp_path: Path):
    from cbc.workspace.staging import create_workspace_lease

    lease = create_workspace_lease(tmp_path)
    assert lease is not None
    assert lease.root.exists()
