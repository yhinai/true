from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import uuid4

from cbc.config import AppConfig, DEFAULT_CONFIG
from cbc.controller.orchestrator import load_adapter
from cbc.model.prompts import write_schema_file
from cbc.models import CodexTaskConfig, OracleSpec, TaskSpec, VerificationOptions

from .toolchains import ToolchainDetection, detect_toolchain


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "into",
    "from",
    "your",
    "have",
    "will",
    "need",
    "make",
    "repo",
    "code",
    "route",
    "file",
}


def build_dynamic_task(
    prompt: str,
    workspace: Path,
    *,
    verify_cmd: str | None = None,
    agent_name: str = "codex",
) -> TaskSpec:
    detection = detect_toolchain(workspace)
    allowed_files = guess_scope_candidates(prompt, workspace, detection=detection)
    oracles = _build_oracles(detection, verify_cmd)
    verification = VerificationOptions(
        lint_command=detection.lint_command or "python3 -m compileall .",
        typecheck_enabled=detection.typecheck_command is not None,
        typecheck_command=detection.typecheck_command,
    )
    task_id = f"solve-{hashlib.sha1(prompt.encode('utf-8')).hexdigest()[:10]}"
    if not allowed_files:
        allowed_files = ["."]
    return TaskSpec(
        task_id=task_id,
        title=prompt.strip()[:120] or "Dynamic solve task",
        prompt=prompt,
        workspace=workspace.resolve(),
        allowed_files=allowed_files,
        required_checks=[oracle.name for oracle in oracles] or ["oracle"],
        doubt_points=[
            "Keep the fix scoped to the relevant files.",
            "Prefer existing tests or deterministic verification over speculative edits.",
        ],
        oracles=oracles,
        adapter=agent_name,
        replay_file=None,
        retry_budget=2,
        timeout_seconds=120,
        tags=detection.languages,
        metadata={
            "dynamic_task": True,
            "toolchains": detection.languages,
            "verify_commands": detection.verify_commands,
        },
        verification=verification,
        codex=CodexTaskConfig(),
    )


def ensure_dynamic_oracle(
    task: TaskSpec,
    *,
    config: AppConfig = DEFAULT_CONFIG,
    agent_name: str = "codex",
) -> TaskSpec:
    if task.oracles:
        return task
    adapter = load_adapter(task, config, agent_name=agent_name)
    oracle_dir = config.paths.artifacts_dir / "dynamic_oracles" / uuid4().hex[:12]
    oracle_dir.mkdir(parents=True, exist_ok=True)
    schema_path = write_schema_file(oracle_dir / "oracle_schema.json")
    prompt = (
        "Write exactly one deterministic verification shell script.\n"
        "The script must exit 0 only when the requested task is satisfied in the current working directory.\n"
        "Do not implement the feature itself.\n"
        "Return one write named generated_verify.sh and mark it executable.\n\n"
        f"Task:\n{task.prompt}\n"
    )
    result = adapter.run(
        prompt=prompt,
        workspace=task.workspace,
        attempt=1,
        candidate_index=0,
        candidate_role="primary",
        schema_path=schema_path,
    )
    write = next((item for item in result.response.writes if Path(item.path).name == "generated_verify.sh"), None)
    if write is None:
        raise RuntimeError("dynamic oracle generation did not return generated_verify.sh")
    oracle_path = oracle_dir / "generated_verify.sh"
    oracle_path.write_text(write.content, encoding="utf-8")
    oracle_path.chmod(0o755)
    return task.model_copy(
        update={
            "oracles": [OracleSpec(name="generated-oracle", kind="shell", command=str(oracle_path))],
            "required_checks": ["generated-oracle"],
            "metadata": {**task.metadata, "generated_oracle": str(oracle_path)},
        }
    )


def guess_scope_candidates(prompt: str, workspace: Path, *, detection: ToolchainDetection, limit: int = 8) -> list[str]:
    keywords = [token for token in _tokenize(prompt) if token not in STOP_WORDS]
    candidates: list[tuple[int, str]] = []
    for path in _iter_candidate_files(workspace):
        rel = path.relative_to(workspace).as_posix()
        score = 0
        lowered = rel.lower()
        for keyword in keywords:
            if keyword in lowered:
                score += 5
        if path.suffix in {".py", ".js", ".ts", ".rs", ".go", ".sh"}:
            score += 1
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")[:4000].lower()
        except OSError:
            content = ""
        for keyword in keywords:
            if keyword in content:
                score += 2
        if score:
            candidates.append((score, rel))
    if candidates:
        ordered = sorted(candidates, key=lambda item: (-item[0], item[1]))
        return [path for _score, path in ordered[:limit]]
    return _default_scope_candidates(workspace, detection=detection, limit=limit)


def _build_oracles(detection: ToolchainDetection, verify_cmd: str | None) -> list[OracleSpec]:
    commands = [verify_cmd] if verify_cmd else detection.verify_commands
    if not commands:
        return []
    oracles: list[OracleSpec] = []
    for index, command in enumerate(commands, start=1):
        if command == "pytest -q":
            oracles.append(OracleSpec(name=f"oracle-{index}", kind="pytest", command="-q"))
        else:
            oracles.append(OracleSpec(name=f"oracle-{index}", kind="shell", command=command))
    return oracles


def _default_scope_candidates(workspace: Path, *, detection: ToolchainDetection, limit: int) -> list[str]:
    suffixes = {
        "python": {".py"},
        "javascript": {".js", ".ts", ".tsx", ".jsx"},
        "rust": {".rs"},
        "go": {".go"},
    }
    accepted_suffixes = set().union(*(suffixes.get(language, set()) for language in detection.languages))
    matches: list[str] = []
    for path in _iter_candidate_files(workspace):
        rel = path.relative_to(workspace).as_posix()
        if not accepted_suffixes or path.suffix in accepted_suffixes:
            matches.append(rel)
        if len(matches) >= limit:
            break
    return matches


def _iter_candidate_files(workspace: Path) -> list[Path]:
    excluded = {".git", ".venv", "node_modules", "__pycache__", "artifacts", "reports", ".mypy_cache", ".pytest_cache"}
    files: list[Path] = []
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        if any(part in excluded for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def _tokenize(prompt: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9_]{3,}", prompt)]
