from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PromptParseResult:
    function_source: str | None = None
    error_info: str | None = None
    context: str | None = None
    source_mode: str = "unknown"
    bug_path: str | None = None
    test_path: str | None = None
    function_path: str | None = None
    parse_confidence: float = 0.0

    @property
    def is_actionable(self) -> bool:
        if self.bug_path:
            return True
        return bool(self.function_source and (self.error_info or self.context))


GUIDANCE = (
    "I need either:\n"
    "- function code + failing test,\n"
    "- function code + stacktrace,\n"
    "- or bug report + function code.\n"
    "Fallback path syntax also works:\n"
    "bug=/abs/path/to/file.py\n"
    "test=/abs/path/to/test.py\n"
    "function=/abs/path/to/file.py\n"
    "stacktrace=/abs/path/to/stacktrace.txt\n"
    "bug_report=/abs/path/to/bug_report.txt"
)


def parse_prompt(text: str) -> PromptParseResult:
    path_mode = _parse_path_mode(text)
    if path_mode is not None:
        return path_mode

    fences = _extract_code_fences(text)
    function_source = _pick_function_block(fences) or _pick_function_block([text])
    error_block = _pick_error_block(fences) or _pick_error_block([text])
    context = _pick_context(text, function_source, error_block)
    source_mode = _infer_source_mode(function_source, error_block, context)
    confidence = 0.0
    if function_source:
        confidence += 0.55
    if error_block:
        confidence += 0.35
    elif context:
        confidence += 0.2

    return PromptParseResult(
        function_source=function_source,
        error_info=error_block,
        context=context,
        source_mode=source_mode,
        parse_confidence=min(confidence, 0.95),
    )


def load_prompt_paths(parsed: PromptParseResult) -> PromptParseResult:
    if parsed.bug_path:
        _read_required_file(parsed.bug_path, "bug")
    if parsed.test_path:
        _read_required_file(parsed.test_path, "test")
    if parsed.function_path:
        parsed.function_source = _read_required_file(parsed.function_path, "function")
    return parsed


def _parse_path_mode(text: str) -> PromptParseResult | None:
    bug_path = None
    test_path = None
    function_path = None
    stacktrace_path = None
    bug_report_path = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "bug":
            bug_path = value
        elif key == "test":
            test_path = value
        elif key == "function":
            function_path = value
        elif key == "stacktrace":
            stacktrace_path = value
        elif key in {"bug_report", "bug-report"}:
            bug_report_path = value

    if not any([bug_path, test_path, function_path, stacktrace_path, bug_report_path]):
        return None

    if bug_path:
        if function_path or stacktrace_path or bug_report_path:
            raise ValueError("Path mode with `bug=` only supports an optional `test=` companion.")
    else:
        if test_path:
            raise ValueError("`test=` requires `bug=` in path mode.")
        if bool(stacktrace_path) == bool(bug_report_path):
            raise ValueError("Path mode requires exactly one of `stacktrace=` or `bug_report=` alongside `function=`.")
        if not function_path:
            raise ValueError("`stacktrace=` and `bug_report=` require `function=` in path mode.")

    error_info = None
    context = None
    if stacktrace_path:
        error_info = _read_required_file(stacktrace_path, "stacktrace")
    if bug_report_path:
        context = _read_required_file(bug_report_path, "bug report")

    return PromptParseResult(
        bug_path=bug_path,
        test_path=test_path,
        function_path=function_path,
        error_info=error_info,
        context=context,
        source_mode="paths",
        parse_confidence=0.95,
    )


def _extract_code_fences(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"```[^\n`]*\n(.*?)```", text, re.DOTALL)]


def _pick_function_block(blocks: list[str]) -> str | None:
    for block in blocks:
        if re.search(r"^\s*(?:async\s+def|def)\s+\w+\s*\(", block, re.MULTILINE):
            return block.strip()
    return None


def _pick_error_block(blocks: list[str]) -> str | None:
    for block in blocks:
        if any(marker in block for marker in ("Traceback", "AssertionError", "FAILED", "E       ", "assert ", "pytest.raises")):
            return block.strip()
        if re.search(r"^\s*def\s+test_\w+\s*\(", block, re.MULTILINE):
            return block.strip()
    return None


def _pick_context(text: str, function_source: str | None, error_info: str | None) -> str | None:
    trimmed = text.strip()
    if not trimmed:
        return None
    context = trimmed
    if function_source:
        context = context.replace(function_source, "").strip()
    if error_info:
        context = context.replace(error_info, "").strip()
    return context or None


def _infer_source_mode(function_source: str | None, error_info: str | None, context: str | None) -> str:
    if function_source and error_info:
        if "traceback" in error_info.lower():
            return "pasted_function_and_stacktrace"
        return "pasted_function_and_test"
    if function_source and context:
        return "pasted_bug_report_and_function"
    return "unknown"


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
