# Phase 2 — ConTree Workspace Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in ConTree-backed workspace adapter so `cbc run --sandbox=contree` runs inside an isolated container with enforced timeouts and zero-cost branching, while the default local-subprocess path is untouched.

**Architecture:** A new `ContreeWorkspace` class wraps the ConTree Python SDK behind a `WorkspaceBackend` protocol. `stage_workspace` in `workspace/staging.py` chooses the backend based on a `SandboxMode` parameter threaded from the CLI. No existing call site changes when `--sandbox=local` (default).

**Tech Stack:** Python 3.11+, `contree-sdk` Python package (async), Typer for CLI flag, pytest + pytest-asyncio for tests. Existing `cbc.workspace.staging.WorkspaceLease` extended, not replaced.

**Prerequisite:** Phase 1 must be merged first (imports `RunState` but does not depend on Phase 1 logic).

---

## File Structure

**New files:**
- `src/cbc/workspace/backends.py` — `WorkspaceBackend` protocol, `LocalBackend`, `SandboxMode` enum
- `src/cbc/workspace/contree_adapter.py` — `ContreeWorkspace` backend
- `tests/workspace/test_backends_protocol.py` — protocol conformance tests
- `tests/workspace/test_contree_adapter.py` — adapter tests (using SDK mock mode)

**Modified files:**
- `src/cbc/workspace/staging.py` — `create_workspace_lease` accepts `sandbox: SandboxMode`
- `src/cbc/main.py` — `run` subcommand adds `--sandbox` flag
- `src/cbc/controller/orchestrator.py` — passes `sandbox` through to `create_workspace_lease`
- `pyproject.toml` — add optional dependency group `[project.optional-dependencies]` → `contree = ["contree-sdk"]`

---

### Task 1: Define `WorkspaceBackend` Protocol and `SandboxMode`

**Files:**
- Create: `src/cbc/workspace/backends.py`
- Test: `tests/workspace/test_backends_protocol.py`

- [ ] **Step 1: Write the failing test**

Create `tests/workspace/test_backends_protocol.py`:

```python
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
```

- [ ] **Step 2: Create `tests/workspace/__init__.py` if missing**

Run: `touch tests/workspace/__init__.py`

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/workspace/test_backends_protocol.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cbc.workspace.backends'`

- [ ] **Step 4: Implement the protocol and local backend**

Create `src/cbc/workspace/backends.py`:

```python
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/workspace/test_backends_protocol.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Lint**

Run: `uv run ruff check src/cbc/workspace/backends.py tests/workspace/test_backends_protocol.py`
Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add src/cbc/workspace/backends.py tests/workspace/test_backends_protocol.py tests/workspace/__init__.py
git commit -m "feat(workspace): add WorkspaceBackend protocol and LocalBackend"
```

---

### Task 2: Add `contree-sdk` Optional Dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Read current `pyproject.toml` deps section**

Read `pyproject.toml` — locate the `[project]` table with `dependencies = [...]`.

- [ ] **Step 2: Add optional dependency group**

Edit `pyproject.toml`, add (or extend) the `[project.optional-dependencies]` table:

```toml
[project.optional-dependencies]
contree = ["contree-sdk"]
```

If the table already exists, add the `contree` key to it without touching other entries.

- [ ] **Step 3: Resolve the optional dep**

Run: `uv sync --extra contree`
Expected: Exit 0. `contree-sdk` installed into the venv. If the package name is different on PyPI, adjust the string (confirm via `pip index versions contree-sdk` or by checking `contree-skill` README) and retry.

- [ ] **Step 4: Verify base install still works without the extra**

Run: `uv sync` (without `--extra contree`)
Expected: Exit 0. `contree-sdk` is NOT installed.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add optional contree-sdk dependency group"
```

---

### Task 3: Implement `ContreeWorkspace` Adapter

**Files:**
- Create: `src/cbc/workspace/contree_adapter.py`
- Test: `tests/workspace/test_contree_adapter.py`

- [ ] **Step 1: Read the ConTree SDK surface**

Read `/tmp/cbc-refs/contree-skill/SKILL.md` lines 215–350 (Python SDK section) for the `images.use`, `image.run`, `disposable`, and `files` patterns.

Key API:
```python
from contree_sdk import Contree
client = Contree(api_key=...)
image = client.images.use("cbc/workspace/<task>:v1")
session = await image.run(shell="...", files={"/work": local_path}, disposable=False, timeout_seconds=N)
```

- [ ] **Step 2: Write the failing test**

Create `tests/workspace/test_contree_adapter.py`:

```python
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from cbc.workspace.backends import SandboxMode, StagedLease


@pytest.mark.asyncio
async def test_contree_workspace_prepare_uses_tagged_image(tmp_path: Path):
    from cbc.workspace.contree_adapter import ContreeWorkspace

    fake_client = MagicMock()
    fake_image = MagicMock()
    fake_image.run = AsyncMock(return_value=MagicMock(image_id="img-1"))
    fake_client.images.use.return_value = fake_image

    ws = ContreeWorkspace(client=fake_client, task_id="t1")
    lease = await ws.prepare_async(tmp_path)

    fake_client.images.use.assert_called_once_with("cbc/workspace/t1:v1")
    assert isinstance(lease, StagedLease)
    assert lease.backend is ws
    assert ws.mode is SandboxMode.CONTREE
```

- [ ] **Step 3: Add `pytest-asyncio` if not already present**

Check `pyproject.toml` for `pytest-asyncio` in the dev dependencies. If missing, add it under `[project.optional-dependencies].dev` (or whatever convention the project uses), then `uv sync`.

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run pytest tests/workspace/test_contree_adapter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cbc.workspace.contree_adapter'`

- [ ] **Step 5: Implement `ContreeWorkspace`**

Create `src/cbc/workspace/contree_adapter.py`:

```python
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
    client: Any
    task_id: str
    version: str = "v1"
    mode: SandboxMode = field(default=SandboxMode.CONTREE, init=False)
    _active_images: dict[Path, str] = field(default_factory=dict, init=False)

    def tag(self) -> str:
        return f"cbc/workspace/{self.task_id}:{self.version}"

    async def prepare_async(self, base_dir: Path) -> StagedLease:
        image = self.client.images.use(self.tag())
        session = await image.run(
            shell="true",
            files={"/work": str(base_dir)},
            disposable=False,
        )
        self._active_images[base_dir] = session.image_id
        return StagedLease(root=Path("/work"), backend=self)

    def prepare(self, base_dir: Path) -> StagedLease:
        # Sync entry point raises: ConTree backend is async-only by design.
        raise RuntimeError(
            "ContreeWorkspace requires the async path; call prepare_async."
        )

    def release(self, lease: StagedLease) -> None:
        # Images are immutable; release is a no-op for the base image.
        # Any branches created during execution are cleaned via their own session teardown.
        return None

    async def execute_async(
        self,
        lease: StagedLease,
        cmd: list[str],
        timeout_seconds: float,
    ) -> ContreeExecResult:
        image_id = self._active_images.get(Path(lease.root))
        image = self.client.images.get(image_id) if image_id else self.client.images.use(self.tag())
        try:
            session = await image.run(
                shell=" ".join(cmd),
                disposable=True,
                timeout_seconds=timeout_seconds,
            )
        except TimeoutError:
            return ContreeExecResult(stdout="", stderr="", returncode=-1, timed_out=True)
        return ContreeExecResult(
            stdout=getattr(session, "stdout", ""),
            stderr=getattr(session, "stderr", ""),
            returncode=getattr(session, "returncode", 0),
        )
```

**Notes for the implementer:**
- The exact SDK surface may differ from the stub above. Adjust `image.run(...)` arguments to the real SDK signature by reading the installed package (`uv run python -c "import contree_sdk; help(contree_sdk.Contree.images)"`).
- `prepare` (sync) raising is intentional: the orchestrator will be the one to decide the event-loop policy.
- The base image represents the prepared task workspace; per-candidate branches are created via `execute_async` with `disposable=True` so siblings don't leak state.

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/workspace/test_contree_adapter.py -v`
Expected: PASS (1 test)

- [ ] **Step 7: Lint**

Run: `uv run ruff check src/cbc/workspace/contree_adapter.py tests/workspace/test_contree_adapter.py`
Expected: No errors.

- [ ] **Step 8: Commit**

```bash
git add src/cbc/workspace/contree_adapter.py tests/workspace/test_contree_adapter.py
git commit -m "feat(workspace): add ContreeWorkspace adapter behind opt-in flag"
```

---

### Task 4: Thread `SandboxMode` Through Staging and Orchestrator

**Files:**
- Modify: `src/cbc/workspace/staging.py`
- Modify: `src/cbc/controller/orchestrator.py`
- Test: add test in `tests/workspace/test_backends_protocol.py`

- [ ] **Step 1: Read current `staging.py`**

Read `src/cbc/workspace/staging.py` (all 26 lines). Understand the `WorkspaceLease` dataclass and `create_workspace_lease` signature.

- [ ] **Step 2: Write the failing test**

Append to `tests/workspace/test_backends_protocol.py`:

```python
def test_create_workspace_lease_defaults_to_local(tmp_path: Path):
    from cbc.workspace.staging import create_workspace_lease

    lease = create_workspace_lease(tmp_path)
    assert lease is not None
    assert lease.root.exists()
```

- [ ] **Step 3: Run test to verify it still passes (no signature change yet)**

Run: `uv run pytest tests/workspace/test_backends_protocol.py::test_create_workspace_lease_defaults_to_local -v`
Expected: PASS (behavior unchanged).

- [ ] **Step 4: Update `create_workspace_lease` signature**

Edit `src/cbc/workspace/staging.py`:

```python
"""Workspace staging with pluggable sandbox backend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cbc.workspace.backends import LocalBackend, SandboxMode, StagedLease


@dataclass
class WorkspaceLease:
    root: Path
    sandbox: SandboxMode
    _staged: StagedLease | None = None

    def release(self) -> None:
        if self._staged is not None:
            self._staged.release()


def create_workspace_lease(
    base_dir: Path,
    *,
    sandbox: SandboxMode = SandboxMode.LOCAL,
) -> WorkspaceLease:
    if sandbox is SandboxMode.LOCAL:
        backend = LocalBackend()
        staged = backend.prepare(base_dir)
        return WorkspaceLease(root=staged.root, sandbox=sandbox, _staged=staged)
    raise NotImplementedError(
        f"Sandbox mode {sandbox} requires async prepare; use create_workspace_lease_async."
    )


async def create_workspace_lease_async(
    base_dir: Path,
    *,
    sandbox: SandboxMode = SandboxMode.LOCAL,
    task_id: str | None = None,
) -> WorkspaceLease:
    if sandbox is SandboxMode.LOCAL:
        return create_workspace_lease(base_dir, sandbox=sandbox)
    if sandbox is SandboxMode.CONTREE:
        from cbc.workspace.contree_adapter import ContreeWorkspace
        from contree_sdk import Contree

        assert task_id is not None, "task_id required for ContreeWorkspace"
        ws = ContreeWorkspace(client=Contree(), task_id=task_id)
        staged = await ws.prepare_async(base_dir)
        return WorkspaceLease(root=staged.root, sandbox=sandbox, _staged=staged)
    raise ValueError(f"Unknown sandbox mode: {sandbox}")


def stage_workspace(base_dir: Path) -> WorkspaceLease:
    return create_workspace_lease(base_dir)
```

**Notes:**
- `WorkspaceLease.root` and `create_workspace_lease(path)` calls elsewhere keep working — only the optional `sandbox=` kwarg is new.
- Existing imports of `WorkspaceLease` are preserved.

- [ ] **Step 5: Run existing workspace + controller tests**

Run: `uv run pytest tests/workspace/ tests/controller/ -v`
Expected: All pass.

- [ ] **Step 6: Thread `sandbox` into `orchestrator.run_task`**

In `src/cbc/controller/orchestrator.py`, change `run_task` signature to accept a `sandbox: SandboxMode = SandboxMode.LOCAL` keyword argument. At the staging site (around line 88 where `create_workspace_lease` is called), pass the sandbox:

```python
if sandbox is SandboxMode.CONTREE:
    workspace_lease = asyncio.run(
        create_workspace_lease_async(task.root, sandbox=sandbox, task_id=task.task_id)
    )
else:
    workspace_lease = create_workspace_lease(task.root, sandbox=sandbox)
```

Add `import asyncio` and import `SandboxMode` and `create_workspace_lease_async` at the top.

- [ ] **Step 7: Run full tests**

Run: `uv run pytest tests/`
Expected: All pass.

- [ ] **Step 8: Commit**

```bash
git add src/cbc/workspace/staging.py src/cbc/controller/orchestrator.py tests/workspace/test_backends_protocol.py
git commit -m "feat(workspace): thread SandboxMode through staging and run_task"
```

---

### Task 5: Add `--sandbox` CLI Flag

**Files:**
- Modify: `src/cbc/main.py`
- Test: `tests/test_main_run_flag.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_main_run_flag.py`:

```python
from typer.testing import CliRunner

from cbc.main import app

runner = CliRunner()


def test_run_accepts_sandbox_local_flag(tmp_path, monkeypatch):
    # Stub run_task so we can assert the sandbox kwarg without actually running.
    captured = {}

    def fake_run_task(task, **kwargs):
        captured.update(kwargs)

        class _R:
            verdict = "VERIFIED"

            def model_dump(self):
                return {"verdict": "VERIFIED"}

        return _R()

    monkeypatch.setattr("cbc.main.run_task", fake_run_task)

    task_file = tmp_path / "task.yaml"
    task_file.write_text("task_id: t1\n")

    monkeypatch.setattr("cbc.main.load_task", lambda p: type("T", (), {"task_id": "t1"})())

    result = runner.invoke(app, ["run", str(task_file), "--sandbox", "local"])
    assert result.exit_code == 0
    assert str(captured.get("sandbox")) in ("SandboxMode.LOCAL", "local", "SandboxMode.local")


def test_run_accepts_sandbox_contree_flag(tmp_path, monkeypatch):
    captured = {}

    def fake_run_task(task, **kwargs):
        captured.update(kwargs)

        class _R:
            def model_dump(self):
                return {"verdict": "VERIFIED"}

        return _R()

    monkeypatch.setattr("cbc.main.run_task", fake_run_task)
    monkeypatch.setattr("cbc.main.load_task", lambda p: type("T", (), {"task_id": "t1"})())

    task_file = tmp_path / "task.yaml"
    task_file.write_text("task_id: t1\n")

    result = runner.invoke(app, ["run", str(task_file), "--sandbox", "contree"])
    assert result.exit_code == 0
    assert "contree" in str(captured.get("sandbox")).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main_run_flag.py -v`
Expected: FAIL (either the flag doesn't exist, or the monkeypatched module path differs).

- [ ] **Step 3: Add the flag**

Edit `src/cbc/main.py` `run` subcommand (lines 30–66). Add parameter:

```python
sandbox: str = typer.Option("local", "--sandbox", help="Sandbox backend: local or contree"),
```

Inside the handler, convert and pass through:

```python
from cbc.workspace.backends import SandboxMode

sandbox_mode = SandboxMode(sandbox)
ledger = run_task(task, ..., sandbox=sandbox_mode)
```

(Replace `...` with the actual existing call arguments.)

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_main_run_flag.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Smoke test local sandbox (default)**

Run: `uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode=treatment --json > /tmp/smoke_local.json`
Expected: Exit 0.

- [ ] **Step 6: Smoke test contree flag (fails without SDK is OK)**

Run: `uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml --mode=treatment --sandbox=contree --json 2>&1 | head -5`

Expected: Either a clear "contree-sdk not installed" error, or the run proceeds if `--extra contree` was installed. Both are acceptable — we are verifying the flag is wired, not the SDK end-to-end.

- [ ] **Step 7: Lint**

Run: `uv run ruff check src/cbc/main.py tests/test_main_run_flag.py`
Expected: No errors.

- [ ] **Step 8: Commit**

```bash
git add src/cbc/main.py tests/test_main_run_flag.py
git commit -m "feat(cli): add --sandbox flag (local|contree) to cbc run"
```

---

### Task 6: End-to-End Oracle Task on ConTree

**Files:**
- Test: `tests/integration/test_contree_e2e.py` (new)

- [ ] **Step 1: Gate the test on the optional extra**

Create `tests/integration/__init__.py` if missing.

Create `tests/integration/test_contree_e2e.py`:

```python
import pytest

contree_sdk = pytest.importorskip("contree_sdk")


@pytest.mark.slow
def test_calculator_bug_runs_under_contree(tmp_path):
    """Opt-in e2e: requires contree-sdk and a reachable ConTree backend."""
    import subprocess

    result = subprocess.run(
        [
            "uv", "run", "cbc", "run",
            "fixtures/oracle_tasks/calculator_bug/task.yaml",
            "--mode=treatment",
            "--sandbox=contree",
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stderr
    assert '"verdict"' in result.stdout
```

- [ ] **Step 2: Ensure pytest has a `slow` marker registered**

Open `pyproject.toml`. Under `[tool.pytest.ini_options]` add (or extend) `markers = ["slow: opt-in integration tests"]`.

- [ ] **Step 3: Confirm default test run skips the slow test**

Run: `uv run pytest tests/ -v -m 'not slow'`
Expected: The contree e2e is not collected (skipped via `importorskip` or the marker).

- [ ] **Step 4: Run with `--extra contree` installed (optional)**

If the real ConTree SDK and backend are accessible, run:

Run: `uv sync --extra contree && uv run pytest tests/integration/test_contree_e2e.py -v -m slow`
Expected: PASS. If no backend is configured, skip this step — the plan does not require a reachable ConTree service.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/__init__.py tests/integration/test_contree_e2e.py pyproject.toml
git commit -m "test(contree): add opt-in e2e oracle task under ContreeWorkspace"
```

---

## Phase 2 Exit Criteria

- `uv run cbc run <task> --sandbox=local` matches pre-Phase-2 behavior
- `uv run cbc run <task> --sandbox=contree` fails gracefully when SDK/backend is missing (clear error, not a traceback)
- `ContreeWorkspace.tag()` returns `cbc/workspace/{task_id}:v1`
- Default `uv sync` does not pull in `contree-sdk`
- All existing tests still pass
- Opt-in e2e test exists under the `slow` marker
