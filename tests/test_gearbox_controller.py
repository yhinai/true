from __future__ import annotations

import json
from pathlib import Path

from cbc.config import AppConfig, PathsConfig, RetryConfig
from cbc.controller.orchestrator import run_task
from cbc.models import OracleSpec, TaskSpec, VerificationVerdict


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_test_config(tmp_path: Path) -> AppConfig:
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
    config.controller.mode = "gearbox"
    return config


def create_task(tmp_path: Path, replay_payload: dict[str, object], *, retry_budget: int = 2) -> TaskSpec:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "calculator.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a - b\n",
        encoding="utf-8",
    )
    (workspace / "test_calculator.py").write_text(
        "from calculator import add\n\n"
        "def test_add() -> None:\n"
        "    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    replay_file = tmp_path / "replay.json"
    replay_file.write_text(json.dumps(replay_payload), encoding="utf-8")
    return TaskSpec(
        task_id="gearbox_case",
        title="Exercise gearbox selection",
        prompt="Fix calculator.add.",
        workspace=workspace,
        allowed_files=["calculator.py"],
        oracles=[OracleSpec(name="pytest", kind="pytest", command="-q")],
        adapter="replay",
        replay_file=replay_file,
        retry_budget=retry_budget,
        tags=["python"],
    )


def test_gearbox_selects_better_candidate_and_retries_selected_path(tmp_path: Path) -> None:
    replay_payload = {
        "attempts": [
            {
                "candidates": [
                    {
                        "summary": "primary candidate introduces a syntax error",
                        "claimed_success": True,
                        "writes": [
                            {"path": "calculator.py", "content": "def add(a: int, b: int) -> int:\n    return\n", "executable": False}
                        ],
                        "notes": [],
                    },
                    {
                        "summary": "alternate candidate keeps the bug",
                        "claimed_success": True,
                        "writes": [
                            {"path": "calculator.py", "content": "def add(a: int, b: int) -> int:\n    return a - b\n", "executable": False}
                        ],
                        "notes": [],
                    },
                ]
            },
            {
                "response": {
                    "summary": "retry fixes the bug",
                    "claimed_success": True,
                    "writes": [
                        {"path": "calculator.py", "content": "def add(a: int, b: int) -> int:\n    return a + b\n", "executable": False}
                    ],
                    "notes": [],
                }
            },
        ]
    }
    task = create_task(tmp_path, replay_payload)
    ledger = run_task(task, mode="treatment", config=build_test_config(tmp_path), controller_mode="gearbox")

    assert ledger.verdict == VerificationVerdict.VERIFIED
    assert ledger.controller_mode == "gearbox"
    assert ledger.selected_candidate_id == "candidate_b"
    assert len(ledger.attempts) == 2
    assert len(ledger.candidate_results) == 2
    assert (ledger.artifact_dir / "scheduler_trace.json").exists()
    assert (ledger.artifact_dir / "risk_artifact.json").exists()
    assert (ledger.artifact_dir / "candidate_artifacts" / "candidate_a" / "verification_report.json").exists()
    assert (ledger.artifact_dir / "candidate_artifacts" / "candidate_b" / "verification_report.json").exists()

    run_artifact = json.loads((ledger.artifact_dir / "run_artifact.json").read_text(encoding="utf-8"))
    assert run_artifact["controller"]["mode"] == "gearbox"
    assert run_artifact["controller"]["selected_candidate_id"] == "candidate_b"
    assert run_artifact["controller"]["budget_spent"]["candidate_evaluations"] == 2
    assert run_artifact["controller"]["budget_spent"]["attempts_executed"] == 2


def test_gearbox_budget_limits_first_attempt_candidates(tmp_path: Path) -> None:
    replay_payload = {
        "attempts": [
            {
                "candidates": [
                    {
                        "summary": "only candidate used under tight budget",
                        "claimed_success": True,
                        "writes": [
                            {"path": "calculator.py", "content": "def add(a: int, b: int) -> int:\n    return a + b\n", "executable": False}
                        ],
                        "notes": [],
                    },
                    {
                        "summary": "would not be reached",
                        "claimed_success": True,
                        "writes": [],
                        "notes": [],
                    },
                ]
            }
        ]
    }
    task = create_task(tmp_path, replay_payload, retry_budget=1)
    config = build_test_config(tmp_path)
    config.controller.budget.max_model_calls_per_run = 1
    config.controller.budget.max_candidates_first_attempt = 2

    ledger = run_task(task, mode="treatment", config=config, controller_mode="gearbox")

    assert ledger.verdict == VerificationVerdict.VERIFIED
    assert len(ledger.candidate_results) == 1

    scheduler_trace = json.loads((ledger.artifact_dir / "scheduler_trace.json").read_text(encoding="utf-8"))
    assert scheduler_trace["model_calls_used"] == 1
    assert scheduler_trace["attempts"][0]["candidate_ids"] == ["candidate_a"]

    run_artifact = json.loads((ledger.artifact_dir / "run_artifact.json").read_text(encoding="utf-8"))
    assert run_artifact["controller"]["budget"]["max_model_calls_per_run"] == 1
    assert run_artifact["controller"]["budget_spent"]["model_calls_used"] == 1
