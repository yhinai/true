"""LLM PR reviewer — posts an advisory Gemini review on each PR event.

Non-blocking by design: does NOT set a check status; just posts a comment.
Reads GEMINI_API_KEY, GH_TOKEN, PR_NUMBER, PR_BASE_SHA, PR_HEAD_SHA, REPO from env.
Never logs the key.
"""

from __future__ import annotations

import os
import subprocess
import sys


MAX_DIFF_CHARS = 60_000  # ~30k tokens for gemini pro
GEMINI_MODEL = "gemini-3.1-pro-preview"


def sh(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True)


def get_diff(base_sha: str, head_sha: str) -> str:
    # Exclude generated artifacts from review to save tokens
    exclude = [
        ":(exclude)artifacts/examples",
        ":(exclude)reports/examples",
        ":(exclude)uv.lock",
        ":(exclude)*.json",
    ]
    return sh(["git", "diff", f"{base_sha}...{head_sha}", "--", "."] + exclude)


def review(diff: str, api_key: str) -> str:
    from google import genai  # type: ignore[import-not-found]
    from google.genai import types  # type: ignore[import-not-found]

    client = genai.Client(api_key=api_key)
    truncated = len(diff) > MAX_DIFF_CHARS
    if truncated:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[...truncated due to size...]"

    system = (
        "You are a senior code reviewer for a Python verification-first control plane. "
        "Be concise. Flag only HIGH-SIGNAL issues: correctness bugs, security risks, "
        "semantic regressions, broken contracts, missing tests for non-trivial logic. "
        "Do NOT nitpick style (ruff already runs). Do NOT restate what the diff does. "
        "If the change looks fine, say so in one line."
    )
    user = (
        "Review the following git diff. Respond in this exact markdown structure:\n\n"
        "**Verdict:** one of `APPROVE`, `COMMENT`, `REQUEST_CHANGES`.\n\n"
        "**Summary:** one sentence.\n\n"
        "**Findings:** bullet list, or `- none` if nothing substantive.\n\n"
        f"```diff\n{diff}\n```"
    )

    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.0,
            max_output_tokens=800,
        ),
    )
    return resp.text or "(no review returned)"


def post_comment(repo: str, pr: str, body: str) -> None:
    # Use gh api so we avoid shell-escaping the markdown body
    url = f"repos/{repo}/issues/{pr}/comments"
    subprocess.run(
        ["gh", "api", url, "--method", "POST", "-f", f"body={body}"],
        check=True,
    )


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY; skipping review.")
        return 0

    base = os.environ["PR_BASE_SHA"]
    head = os.environ["PR_HEAD_SHA"]
    repo = os.environ["REPO"]
    pr = os.environ["PR_NUMBER"]

    diff = get_diff(base, head)
    if not diff.strip():
        print("Empty diff; skipping.")
        return 0

    try:
        body = review(diff, api_key)
    except Exception as e:
        print(f"Gemini call failed: {e}")
        return 0  # non-blocking

    body = f"## Automated review\n\n{body}\n\n---\n*Advisory only — CI tests remain authoritative.*"
    try:
        post_comment(repo, pr, body)
    except subprocess.CalledProcessError as e:
        print(f"gh api comment post failed: {e}")
        return 0
    print("Review posted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
