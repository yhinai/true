"""LLM-powered merge-conflict auto-resolver.

Run by .github/workflows/llm-conflict-resolver.yml on a schedule.
Requires GEMINI_API_KEY, GH_TOKEN, REPO env vars.
Never logs or commits the Gemini key.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

GEMINI_MODEL = "gemini-3.1-flash-lite-preview"


def sh(cmd: list[str], *, cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=check)


def list_candidate_prs(repo: str) -> list[dict]:
    res = sh([
        "gh", "pr", "list", "--repo", repo, "--state", "open", "--base", "main",
        "--label", "conflict-needs-review",
        "--json", "number,headRefName,headRepositoryOwner",
    ])
    data = json.loads(res.stdout or "[]")
    owner = repo.split("/")[0]
    return [pr for pr in data if pr.get("headRepositoryOwner", {}).get("login") == owner]


def resolve_one_conflict(ancestor: str, ours: str, theirs: str, path: str, client) -> str:
    from google.genai import types  # type: ignore[import-not-found]

    system_instruction = "You merge code conflicts deterministically."
    user_prompt = (
        "You are a code-merge assistant. Produce the fully resolved file content that preserves the intent of both branches.\n\n"
        f"File path: {path}\n\n"
        f"=== COMMON ANCESTOR ===\n{ancestor}\n\n"
        f"=== HEAD (our PR branch) ===\n{ours}\n\n"
        f"=== ORIGIN/MAIN (incoming) ===\n{theirs}\n\n"
        "Output ONLY the final merged file contents. No prose, no code fences, no commentary."
    )
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
        ),
    )
    return resp.text or ""


def process_pr(pr: dict, repo: str, client) -> None:
    num = pr["number"]
    branch = pr["headRefName"]
    print(f"=== PR #{num} on {branch} ===")

    tmp = tempfile.mkdtemp()
    remote = f"https://x-access-token:{os.environ['GH_TOKEN']}@github.com/{repo}.git"
    sh(["git", "clone", "--quiet", remote, tmp])
    sh(["git", "-C", tmp, "config", "user.name", "cbc-auto-refresh[bot]"])
    sh(["git", "-C", tmp, "config", "user.email", "cbc-auto-refresh[bot]@users.noreply.github.com"])
    sh(["git", "-C", tmp, "fetch", "origin", f"{branch}:{branch}", "main"])
    sh(["git", "-C", tmp, "checkout", branch])

    merge = sh(["git", "-C", tmp, "merge", "--no-commit", "--no-ff", "origin/main"], check=False)
    if merge.returncode == 0:
        print("  3-way merge clean; pushing.")
        sh(["git", "-C", tmp, "commit", "--no-edit"], check=False)
        sh(["git", "-C", tmp, "push", "origin", branch])
        sh(["gh", "pr", "edit", "--repo", repo, str(num), "--remove-label", "conflict-needs-review", "--add-label", "resolver-succeeded"], check=False)
        return

    conflicted = sh(["git", "-C", tmp, "diff", "--name-only", "--diff-filter=U"]).stdout.split()
    print(f"  conflicted files: {conflicted}")
    if len(conflicted) > 5:
        print("  too many conflicts; skipping.")
        sh(["git", "-C", tmp, "merge", "--abort"], check=False)
        sh(["gh", "pr", "edit", "--repo", repo, str(num), "--remove-label", "conflict-needs-review", "--add-label", "resolver-failed"], check=False)
        return

    for path in conflicted:
        try:
            anc = sh(["git", "-C", tmp, "show", f":1:{path}"], check=False).stdout
            ours = sh(["git", "-C", tmp, "show", f":2:{path}"], check=False).stdout
            theirs = sh(["git", "-C", tmp, "show", f":3:{path}"], check=False).stdout
        except Exception as e:
            print(f"  git show failed for {path}: {e}")
            sh(["git", "-C", tmp, "merge", "--abort"], check=False)
            return

        # Cap at 50k chars per side to stay within context
        if max(len(anc), len(ours), len(theirs)) > 50_000:
            print(f"  {path} too large for LLM; bailing.")
            sh(["git", "-C", tmp, "merge", "--abort"], check=False)
            sh(["gh", "pr", "edit", "--repo", repo, str(num), "--remove-label", "conflict-needs-review", "--add-label", "resolver-failed"], check=False)
            return

        resolved = resolve_one_conflict(anc, ours, theirs, path, client)
        Path(tmp, path).write_text(resolved)
        sh(["git", "-C", tmp, "add", path])

    # Commit the merge
    sh(["git", "-C", tmp, "commit", "--no-edit"])

    # Gate on tests
    print("  running test gate...")
    tests = sh(["bash", "-lc", "cd '" + tmp + "' && uv sync --extra dev && uv run pytest tests/ -m 'not slow' -q"], check=False)
    if tests.returncode != 0:
        print(f"  TESTS FAILED after LLM merge:\n{tests.stdout[-2000:]}\n{tests.stderr[-2000:]}")
        sh(["gh", "pr", "edit", "--repo", repo, str(num), "--remove-label", "conflict-needs-review", "--add-label", "resolver-failed"], check=False)
        return

    print("  tests green; pushing.")
    sh(["git", "-C", tmp, "push", "origin", branch])
    sh(["gh", "pr", "edit", "--repo", repo, str(num), "--remove-label", "conflict-needs-review", "--add-label", "resolver-succeeded"], check=False)


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY; skipping.")
        return 0

    from google import genai  # type: ignore[import-not-found]

    repo = os.environ["REPO"]
    prs = list_candidate_prs(repo)
    if not prs:
        print("No conflicting PRs needing LLM resolution.")
        return 0

    client = genai.Client(api_key=api_key)
    for pr in prs:
        try:
            process_pr(pr, repo, client)
        except Exception as e:
            print(f"  error processing PR #{pr['number']}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
