from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from cbc.benchmark.local_runner import run_local_benchmark, run_local_controller_benchmark
from cbc.config import AppConfig, PathsConfig
from cbc.controller.orchestrator import run_task
from cbc.intake.normalize import load_task


FIXED_START = "2026-04-18T00:00:00Z"
FIXED_END = "2026-04-18T00:00:01Z"


def refresh_examples(repo_root: Path) -> dict[str, str]:
    repo_root = repo_root.resolve()
    with tempfile.TemporaryDirectory(prefix="cbc-example-refresh-") as temp_dir:
        temp_root = Path(temp_dir)
        config = AppConfig(
            paths=PathsConfig(
                root=repo_root,
                artifacts_dir=temp_root / "artifacts",
                reports_dir=temp_root / "reports",
                prompts_dir=repo_root / "prompts",
                benchmark_config_dir=repo_root / "benchmark-configs",
                storage_db=temp_root / "artifacts" / "cbc.sqlite3",
            )
        )

        calculator = load_task(repo_root / "fixtures/oracle_tasks/calculator_bug/task.yaml")
        calculator_ledger = run_task(calculator, mode="treatment", config=config, controller_mode="gearbox")
        slugify = load_task(repo_root / "fixtures/oracle_tasks/slugify_property_regression/task.yaml")
        slugify_ledger = run_task(slugify, mode="treatment", config=config)
        curated_benchmark = run_local_benchmark(repo_root / "benchmark-configs/curated_subset.yaml", config=config)
        expanded_benchmark = run_local_benchmark(repo_root / "benchmark-configs/expanded_subset.yaml", config=config)
        controller_benchmark = run_local_controller_benchmark(
            repo_root / "benchmark-configs/controller_subset.yaml",
            config=config,
        )

        destinations = {
            "calculator_treatment": repo_root / "artifacts/examples/calculator_treatment",
            "slugify_property_regression_treatment": repo_root / "artifacts/examples/slugify_property_regression_treatment",
            "curated_benchmark": repo_root / "reports/examples/curated_benchmark",
            "expanded_benchmark": repo_root / "reports/examples/expanded_benchmark",
            "controller_benchmark": repo_root / "reports/examples/controller_benchmark",
        }

        _replace_tree(
            calculator_ledger.artifact_dir,
            destinations["calculator_treatment"],
            repo_root=repo_root,
            example_id="example-calculator-treatment",
            example_dir=Path("artifacts/examples/calculator_treatment"),
        )
        _replace_tree(
            slugify_ledger.artifact_dir,
            destinations["slugify_property_regression_treatment"],
            repo_root=repo_root,
            example_id="example-slugify-property-regression-treatment",
            example_dir=Path("artifacts/examples/slugify_property_regression_treatment"),
        )
        _replace_tree(
            curated_benchmark.report_dir,
            destinations["curated_benchmark"],
            repo_root=repo_root,
            example_id="example-curated-benchmark",
            example_dir=Path("reports/examples/curated_benchmark"),
        )
        _replace_tree(
            expanded_benchmark.report_dir,
            destinations["expanded_benchmark"],
            repo_root=repo_root,
            example_id="example-expanded-benchmark",
            example_dir=Path("reports/examples/expanded_benchmark"),
        )
        _replace_tree(
            controller_benchmark.report_dir,
            destinations["controller_benchmark"],
            repo_root=repo_root,
            example_id="example-controller-benchmark",
            example_dir=Path("reports/examples/controller_benchmark"),
        )
    return {name: str(path) for name, path in destinations.items()}


def _replace_tree(
    source: Path,
    destination: Path,
    *,
    repo_root: Path,
    example_id: str,
    example_dir: Path,
) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if item.suffix == ".json":
            payload = json.loads(item.read_text(encoding="utf-8"))
            normalized = _normalize_json_payload(
                payload,
                source_root=source,
                repo_root=repo_root,
                example_id=example_id,
                example_dir=example_dir,
            )
            target.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
        elif item.suffix in {".md", ".txt"}:
            content = item.read_text(encoding="utf-8")
            target.write_text(
                _normalize_text_content(
                    content,
                    source_root=source,
                    repo_root=repo_root,
                    example_id=example_id,
                    example_dir=example_dir,
                ),
                encoding="utf-8",
            )
        else:
            shutil.copy2(item, target)


def _normalize_json_payload(
    payload: Any,
    *,
    source_root: Path,
    repo_root: Path,
    example_id: str,
    example_dir: Path,
) -> Any:
    normalized = _walk_normalize(payload, source_root=source_root, repo_root=repo_root, example_dir=example_dir)
    if isinstance(normalized, dict):
        if "run_id" in normalized:
            normalized["run_id"] = example_id
        if "benchmark_id" in normalized:
            normalized["benchmark_id"] = example_id
        if "poc_id" in normalized:
            normalized["poc_id"] = example_id
    return normalized


def _walk_normalize(value: Any, *, source_root: Path, repo_root: Path, example_dir: Path) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key == "artifact_dir":
                result[key] = example_dir.as_posix()
                continue
            if key == "report_dir":
                result[key] = example_dir.as_posix()
                continue
            if key == "workspace_dir":
                result[key] = "<staged_workspace>"
                continue
            if key == "run_id":
                result[key] = "normalized-run-id"
                continue
            if key == "benchmark_id":
                result[key] = "normalized-benchmark-id"
                continue
            if key in {"started_at", "created_at"}:
                result[key] = FIXED_START
                continue
            if key == "ended_at":
                result[key] = FIXED_END
                continue
            if key == "selected_candidate_id" and item is None:
                result[key] = None
                continue
            result[key] = _walk_normalize(item, source_root=source_root, repo_root=repo_root, example_dir=example_dir)
        return result
    if isinstance(value, list):
        return [_walk_normalize(item, source_root=source_root, repo_root=repo_root, example_dir=example_dir) for item in value]
    if isinstance(value, str):
        return _normalize_string(
            value,
            source_root=source_root,
            repo_root=repo_root,
            example_dir=example_dir,
        )
    return value


def _normalize_text_content(
    content: str,
    *,
    source_root: Path,
    repo_root: Path,
    example_id: str,
    example_dir: Path,
) -> str:
    content = content.replace(str(source_root), example_dir.as_posix())
    content = content.replace(str(repo_root), "<repo>")
    content = content.replace("`" + example_id + "`", "`" + example_id + "`")
    content = re.sub(r"`[0-9a-f]{12}`", f"`{example_id}`", content)
    content = _normalize_temp_paths(content)
    return content


def _normalize_string(value: str, *, source_root: Path, repo_root: Path, example_dir: Path) -> str:
    normalized = value.replace(str(source_root), example_dir.as_posix())
    normalized = normalized.replace(str(repo_root), "<repo>")
    normalized = _normalize_temp_paths(normalized)
    normalized = re.sub(r"(^|/)([0-9a-f]{12})(?=/|$)", r"\1<runtime-id>", normalized)
    return normalized


def _normalize_temp_paths(value: str) -> str:
    value = re.sub(r"/var/folders/[^ ]+/cbc-workspace-[^ /]+/workspace", "<staged_workspace>", value)
    value = re.sub(r"/tmp/[^ ]+", "<temp_path>", value)
    value = re.sub(r"/private/var/folders/[^ ]+/cbc-workspace-[^ /]+/workspace", "<staged_workspace>", value)
    return value
