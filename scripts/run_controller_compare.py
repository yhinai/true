#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = Path(__file__).resolve()
SRC_ROOT = REPO_ROOT / "src"
BOOTSTRAP_ENV_VAR = "CBC_RUN_CONTROLLER_COMPARE_BOOTSTRAPPED"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class Runtime(NamedTuple):
    run_local_controller_benchmark: Callable[..., Any]
    render_controller_benchmark_markdown: Callable[[Any], str]
    AppConfig: type[Any]
    PathsConfig: type[Any]


def _load_runtime(argv: list[str]) -> Runtime:
    try:
        from cbc.benchmark.local_runner import run_local_controller_benchmark
        from cbc.benchmark.reports import render_controller_benchmark_markdown
        from cbc.config import AppConfig, PathsConfig
    except ModuleNotFoundError as exc:
        _bootstrap_with_uv(argv, exc)
        raise
    return Runtime(
        run_local_controller_benchmark=run_local_controller_benchmark,
        render_controller_benchmark_markdown=render_controller_benchmark_markdown,
        AppConfig=AppConfig,
        PathsConfig=PathsConfig,
    )


def _bootstrap_with_uv(argv: list[str], exc: ModuleNotFoundError) -> None:
    if os.environ.get(BOOTSTRAP_ENV_VAR):
        return
    missing_module = exc.name or "unknown dependency"
    uv_command = _resolve_uv_command()
    if uv_command is None:
        raise SystemExit(
            "Direct invocation is missing "
            f"{missing_module!r}. Run `uv run --project {REPO_ROOT} python3 {SCRIPT_PATH}` "
            "or install the project dependencies first."
        ) from exc

    print(
        "Direct invocation is missing "
        f"{missing_module!r}; re-running with `uv run` in the repo environment.",
        file=sys.stderr,
    )
    env = os.environ.copy()
    env[BOOTSTRAP_ENV_VAR] = missing_module
    os.execvpe(
        uv_command[0],
        [
            *uv_command,
            "run",
            "--project",
            str(REPO_ROOT),
            "--frozen",
            "--extra",
            "dev",
            "python3",
            str(SCRIPT_PATH),
            *argv,
        ],
        env,
    )


def _resolve_uv_command() -> list[str] | None:
    uv_path = shutil.which("uv")
    if uv_path is not None:
        return [uv_path]

    python_candidates = [
        shutil.which("python3"),
        shutil.which("python"),
        "/usr/bin/python3",
        sys.executable,
    ]
    for candidate in python_candidates:
        if not candidate:
            continue
        probe = subprocess.run(
            [candidate, "-m", "uv", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode == 0:
            return [candidate, "-m", "uv"]
    return None


def build_config(artifacts_root: Path, reports_root: Path, runtime: Runtime) -> Any:
    return runtime.AppConfig(
        paths=runtime.PathsConfig(
            root=REPO_ROOT,
            artifacts_dir=artifacts_root,
            reports_dir=reports_root,
            prompts_dir=REPO_ROOT / "prompts",
            benchmark_config_dir=REPO_ROOT / "benchmark-configs",
            storage_db=artifacts_root / "cbc.sqlite3",
        )
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run sequential vs gearbox controller comparison.",
        epilog=(
            "If the current interpreter is missing repo dependencies, the script re-runs "
            "itself through `uv run`."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("benchmark-configs/controller_subset.yaml"),
        help="Path to controller comparison config.",
    )
    parser.add_argument("--artifacts-root", type=Path, default=Path("artifacts"))
    parser.add_argument("--reports-root", type=Path, default=Path("reports"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    cli_args = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(cli_args)
    runtime = _load_runtime(cli_args)
    config_path = (REPO_ROOT / args.config).resolve() if not args.config.is_absolute() else args.config
    artifacts_root = (REPO_ROOT / args.artifacts_root).resolve() if not args.artifacts_root.is_absolute() else args.artifacts_root
    reports_root = (REPO_ROOT / args.reports_root).resolve() if not args.reports_root.is_absolute() else args.reports_root
    app_config = build_config(artifacts_root, reports_root, runtime)
    comparison = runtime.run_local_controller_benchmark(config_path, config=app_config)

    output_dir = reports_root / "controller-compare"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_output = output_dir / "compare.json"
    markdown_output = output_dir / "compare.md"
    json_output.write_text(json.dumps(comparison.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_output.write_text(runtime.render_controller_benchmark_markdown(comparison), encoding="utf-8")

    print(f"comparison json: {json_output}")
    print(f"comparison report: {markdown_output}")
    print(
        json.dumps(
            {
                "recommended_controller": comparison.decision.recommended_controller,
                "should_promote_to_default": comparison.decision.should_promote_to_default,
                "delta_verified_success_rate": comparison.delta_verified_success_rate,
                "delta_average_model_calls": comparison.delta_average_model_calls,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
