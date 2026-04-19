from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cbc.main import app
from cbc.workspace.backends import InPlaceBackend, SandboxMode
from cbc.workspace.staging import create_workspace_lease


REPO_ROOT = Path(__file__).resolve().parents[2]
CALCULATOR_WORKSPACE = REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/workspace"
CALCULATOR_TASK = REPO_ROOT / "fixtures/oracle_tasks/calculator_bug/task.yaml"


def test_inplace_backend_prepare_returns_same_path(tmp_path: Path) -> None:
    backend = InPlaceBackend(tmp_path)
    lease = backend.prepare(tmp_path)
    assert lease.root == tmp_path
    assert lease.root.exists()


def test_inplace_backend_cleanup_leaves_files(tmp_path: Path) -> None:
    (tmp_path / "marker.txt").write_text("keep me", encoding="utf-8")
    backend = InPlaceBackend(tmp_path)
    lease = backend.prepare(tmp_path)
    backend.release(lease)
    assert (tmp_path / "marker.txt").read_text(encoding="utf-8") == "keep me"
    assert tmp_path.exists()


def test_inplace_backend_rejects_missing_dir(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    backend = InPlaceBackend(missing)
    with pytest.raises(FileNotFoundError):
        backend.prepare(missing)


def test_create_workspace_lease_inplace_no_copy(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("x", encoding="utf-8")
    lease = create_workspace_lease(
        tmp_path, sandbox=SandboxMode.INPLACE, inplace_root=tmp_path
    )
    assert lease.sandbox is SandboxMode.INPLACE
    assert lease.root == tmp_path
    assert lease.path == tmp_path
    # cleanup must be a no-op
    lease.cleanup()
    assert (tmp_path / "file.txt").exists()


def test_run_task_inplace_edits_target_dir(tmp_path: Path) -> None:
    from cbc.config import AppConfig, PathsConfig, RetryConfig
    from cbc.controller.orchestrator import run_task
    from cbc.intake.normalize import load_task
    from cbc.models import VerificationVerdict

    # Copy the calculator workspace into a tmp dir the run will edit directly.
    target = tmp_path / "repo" / "workspace"
    shutil.copytree(CALCULATOR_WORKSPACE, target)

    config = AppConfig(
        paths=PathsConfig(
            root=REPO_ROOT,
            artifacts_dir=tmp_path / "artifacts",
            reports_dir=tmp_path / "reports",
            prompts_dir=REPO_ROOT / "prompts",
            benchmark_config_dir=REPO_ROOT / "benchmark-configs",
            storage_db=tmp_path / "artifacts" / "cbc.sqlite3",
        ),
        retry=RetryConfig(max_attempts=2),
    )

    task = load_task(CALCULATOR_TASK)
    ledger = run_task(
        task,
        mode="treatment",
        config=config,
        sandbox=SandboxMode.INPLACE,
        inplace_root=target,
    )

    assert ledger.verdict == VerificationVerdict.VERIFIED
    # In-place: the target dir must still exist (no cleanup) and carry the fix.
    assert target.exists()
    calc = (target / "calculator.py").read_text(encoding="utf-8")
    assert "a + b" in calc


def test_cli_workspace_in_place_rejects_home(tmp_path: Path) -> None:
    runner = CliRunner()
    home = Path(os.path.expanduser("~"))
    result = runner.invoke(
        app,
        ["run", str(CALCULATOR_TASK), "--workspace-in-place", str(home)],
    )
    assert result.exit_code != 0
    assert "workspace-in-place" in (result.output + (result.stderr or ""))


def test_cli_workspace_in_place_and_sandbox_mutually_exclusive(tmp_path: Path) -> None:
    runner = CliRunner()
    target = tmp_path / "repo" / "workspace"
    shutil.copytree(CALCULATOR_WORKSPACE, target)
    result = runner.invoke(
        app,
        [
            "run",
            str(CALCULATOR_TASK),
            "--workspace-in-place",
            str(target),
            "--sandbox",
            "local",
        ],
    )
    assert result.exit_code != 0
    combined = result.output + (result.stderr or "")
    assert "mutually exclusive" in combined
