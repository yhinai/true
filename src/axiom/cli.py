from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .pipeline import AxiomPipeline, PipelineInput


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="axiom-cli")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bug", help="Path to the Python file containing the target function.")
    mode.add_argument("--stacktrace", help="Path to a stacktrace or failing output text file.")
    mode.add_argument("--bug-report", help="Path to a natural-language bug report file.")
    parser.add_argument("--test", help="Path to a pytest file to run after patching.")
    parser.add_argument("--function", help="Path to the Python file containing the target function for stacktrace or bug-report mode.")
    parser.add_argument("--force-unproven", action="store_true", help="Force the ledger into the UNPROVEN path.")
    parser.add_argument("--verify-original", action="store_true", help="Skip patch application and verify the original source.")
    return parser


def _read_required_file(path: str, label: str) -> str:
    candidate = Path(path)
    if not candidate.exists():
        raise FileNotFoundError(f"{label.capitalize()} file not found: {path}")
    if not candidate.is_file():
        raise ValueError(f"{label.capitalize()} path is not a file: {path}")
    content = candidate.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"{label.capitalize()} file is empty: {path}")
    return content


def _build_pipeline_input(args: argparse.Namespace) -> PipelineInput:
    if args.bug:
        if args.function:
            raise ValueError("`--function` cannot be combined with `--bug`; pass the function file with `--bug` directly.")
        return PipelineInput(
            bug_source_path=args.bug,
            test_path=args.test,
            run_tests=bool(args.test),
            verify_original=args.verify_original,
        )

    if args.stacktrace:
        if args.test:
            raise ValueError("`--test` is only supported with `--bug` mode.")
        if not args.function:
            raise ValueError("`--stacktrace` requires `--function`.")
        return PipelineInput(
            bug_source_path=args.function,
            function_source=_read_required_file(args.function, "function"),
            bug_text=_read_required_file(args.stacktrace, "stacktrace"),
            run_tests=False,
            verify_original=args.verify_original,
        )

    if args.bug_report:
        if args.test:
            raise ValueError("`--test` is only supported with `--bug` mode.")
        if not args.function:
            raise ValueError("`--bug-report` requires `--function`.")
        return PipelineInput(
            bug_source_path=args.function,
            function_source=_read_required_file(args.function, "function"),
            bug_text=_read_required_file(args.bug_report, "bug report"),
            run_tests=False,
            verify_original=args.verify_original,
        )

    raise ValueError("One of `--bug`, `--stacktrace`, or `--bug-report` is required.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        pipeline_input = _build_pipeline_input(args)
        pipeline = AxiomPipeline()
        ledger = pipeline.run_and_render(
            pipeline_input,
            force_unproven=args.force_unproven,
        )
        print(ledger)
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(f"axiom-cli: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
