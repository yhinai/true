#!/usr/bin/env bash
# scripts/push-via-pr.sh — push current local commits to a feature branch + open an auto-merging PR.
# Usage: scripts/push-via-pr.sh [branch-slug]
# Requires: gh CLI authenticated with repo:write scope.
set -euo pipefail

SLUG="${1:-auto-$(date +%Y%m%d-%H%M%S)}"
BRANCH="pr/${SLUG}"

# Refuse if working tree is dirty
if [[ -n "$(git status --porcelain)" ]]; then
    echo "Error: working tree not clean. Commit or stash first." >&2
    exit 1
fi

# Refuse if there are no commits ahead of origin/main
AHEAD=$(git rev-list --count origin/main..HEAD)
if [[ "$AHEAD" -eq 0 ]]; then
    echo "No commits to push." >&2
    exit 0
fi

# Capture original branch so we can return to it
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Create feature branch at current HEAD
git branch "$BRANCH"
git push -u origin "$BRANCH"

# Compose PR body from recent commits
TITLE=$(git log -1 --pretty=format:"%s")
BODY=$(git log origin/main..HEAD --pretty=format:"- %s" --reverse)

# Open PR (draft=false, no assignee)
gh pr create \
    --base main \
    --head "$BRANCH" \
    --title "$TITLE" \
    --body "$BODY"

# Enable auto-merge on the PR (squash strategy)
gh pr merge --auto --squash "$BRANCH"

# Return to original branch (main) and reset its pointer to origin/main so further work starts clean
if [[ "$ORIGINAL_BRANCH" == "main" ]]; then
    git reset --hard "origin/main"
else
    git checkout "$ORIGINAL_BRANCH"
fi

echo "PR opened on branch $BRANCH; auto-merge enabled."
