#!/usr/bin/env python3
import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(base: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()


def render_proof_card(verification: dict) -> str:
    verdict = "PASS" if verification["passed"] else "FAIL"
    allowed_paths = ", ".join(verification["allowed_paths"])
    oracle_command = " ".join(verification["oracle_command"])
    lines = [
        f"# Proof Card: {verification['task_id']}",
        "",
        f"- Verdict: `{verdict}`",
        f"- Suite: `{verification['suite']}`",
        f"- Candidate source: `{verification['candidate_source']}`",
        f"- Oracle kind: `{verification['oracle_kind']}`",
        f"- Oracle command: `{oracle_command}`",
        f"- Allowed paths: `{allowed_paths}`",
        f"- Duration ms: `{verification['duration_ms']}`",
        f"- Started at: `{verification['started_at']}`",
        "",
        "## Prompt",
        "",
        verification["prompt"].rstrip(),
        "",
    ]

    if verification["stdout"]:
        lines.extend(
            [
                "## Oracle stdout",
                "",
                "```text",
                verification["stdout"].rstrip(),
                "```",
                "",
            ]
        )

    if verification["stderr"]:
        lines.extend(
            [
                "## Oracle stderr",
                "",
                "```text",
                verification["stderr"].rstrip(),
                "```",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


@dataclass
class TaskResult:
    task_id: str
    title: str
    passed: bool
    exit_code: int
    duration_ms: int
    verification_path: str
    proof_card_path: Optional[str]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stage fixture candidates, run deterministic oracles, and write suite reports."
    )
    parser.add_argument("--config", required=True, help="Path to a benchmark config file.")
    parser.add_argument(
        "--candidate-source",
        choices=("workspace", "solution"),
        help="Override the configured candidate source.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where reports and staged candidates will be written.",
    )
    parser.add_argument(
        "--render-proof-cards",
        action="store_true",
        help="Render proof cards even when the config does not require them.",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    output_dir = Path(args.output_dir).resolve()
    config = load_json(config_path)
    subset_path = resolve_path(config_path.parent, config["subset_config"])
    subset = load_json(subset_path)

    candidate_source = args.candidate_source or config["smoke_verification"]["candidate_source"]
    emit_proof_cards = args.render_proof_cards or config["policy"]["require_proof_card"]

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    task_results: List[TaskResult] = []
    started_at = utc_now()

    for task_entry in subset["tasks"]:
        manifest_path = resolve_path(subset_path.parent, task_entry["manifest"])
        task_dir = manifest_path.parent
        manifest = load_json(manifest_path)
        prompt_path = resolve_path(task_dir, manifest["prompt_file"])
        prompt = prompt_path.read_text(encoding="utf-8")

        candidate_root = resolve_path(task_dir, manifest[f"{candidate_source}_dir"])
        task_output_dir = output_dir / "tasks" / manifest["id"]
        task_output_dir.mkdir(parents=True, exist_ok=True)

        command = manifest["oracle"]["command"]
        with tempfile.TemporaryDirectory(prefix=f"{config['name']}-{manifest['id']}-") as temp_dir:
            candidate_dir = Path(temp_dir) / "candidate"
            shutil.copytree(candidate_root, candidate_dir)

            env = os.environ.copy()
            env.update(
                {
                    "CANDIDATE_DIR": str(candidate_dir),
                    "TASK_DIR": str(task_dir),
                    "SUITE_NAME": config["name"],
                }
            )

            verification_started_at = utc_now()
            start_time = time.perf_counter()
            completed = subprocess.run(
                command,
                cwd=task_dir,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)

        verification = {
            "suite": config["name"],
            "task_id": manifest["id"],
            "title": manifest["title"],
            "candidate_source": candidate_source,
            "staged_from": str(candidate_root),
            "task_dir": str(task_dir),
            "prompt": prompt,
            "allowed_paths": manifest["allowed_paths"],
            "oracle_kind": manifest["oracle"]["kind"],
            "oracle_command": command,
            "started_at": verification_started_at,
            "duration_ms": duration_ms,
            "exit_code": completed.returncode,
            "passed": completed.returncode == 0,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

        verification_path = task_output_dir / "verification.json"
        verification_path.write_text(
            json.dumps(verification, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        proof_card_path = None
        if emit_proof_cards:
            proof_card_path = task_output_dir / "proof-card.md"
            proof_card_path.write_text(render_proof_card(verification), encoding="utf-8")

        task_results.append(
            TaskResult(
                task_id=manifest["id"],
                title=manifest["title"],
                passed=verification["passed"],
                exit_code=completed.returncode,
                duration_ms=duration_ms,
                verification_path=str(verification_path),
                proof_card_path=str(proof_card_path) if proof_card_path else None,
            )
        )

    passed = sum(1 for result in task_results if result.passed)
    summary = {
        "suite": config["name"],
        "description": config["description"],
        "config_path": str(config_path),
        "subset_path": str(subset_path),
        "candidate_source": candidate_source,
        "started_at": started_at,
        "completed_at": utc_now(),
        "task_count": len(task_results),
        "passed": passed,
        "failed": len(task_results) - passed,
        "verified_success_rate": passed / len(task_results) if task_results else 0.0,
        "policy": config["policy"],
        "budget": config["budget"],
        "golden_task_ids": subset["golden_task_ids"],
        "tasks": [asdict(result) for result in task_results],
        "note": (
            "This suite verifies fixture oracles against the checked-in candidate source. "
            "It does not execute a Codex adapter yet."
        ),
    }

    summary_path = output_dir / "suite-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "suite": summary["suite"],
                "task_count": summary["task_count"],
                "passed": summary["passed"],
                "failed": summary["failed"],
                "summary_path": str(summary_path),
            },
            sort_keys=True,
        )
    )
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
