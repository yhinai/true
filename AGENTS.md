# Repository AGENTS.md

This repository follows a push-forward workflow. Treat verified progress as something that should be recorded and synchronized, not left only in the local worktree.

## Git Workflow

- Work on `main` unless explicitly told otherwise.
- Keep the local branch synchronized with `origin/main`.
- Before pushing, if the remote may have moved, fetch and reconcile first.
- If a push is rejected because the remote changed, run `git pull --rebase origin main`, resolve any conflicts carefully, re-verify, and push again.
- Do not leave substantial verified work uncommitted locally.

## Commit And Push Rules

- After any substantial change that has been verified, create a git commit with a clear message and push it.
- After any milestone is reached, create a git commit with a clear message and push it.
- After any verification pass that proves the current implementation works for the intended change, commit and push that state.
- Prefer small, truthful commits over large delayed batches.
- Commit messages should describe the verified outcome, not vague activity.

## Verification Gate

- Do not commit or push code that has not been verified in the most relevant way available for the task.
- Verification can include tests, linters, type checks, build checks, or another deterministic oracle appropriate to the change.
- If verification fails, fix the issue first, then commit and push only after the passing state is restored.

## Safety Rules

- Never overwrite or discard user changes just to make syncing easier.
- If the worktree contains unrelated user changes, isolate your own changes carefully before committing.
- If synchronization requires conflict resolution, preserve the verified behavior before pushing.
