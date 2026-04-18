from __future__ import annotations

from cbc.models import ReviewReport


def render_pr_comment(review: ReviewReport) -> str:
    risks = "\n".join(f"- {risk}" for risk in review.risks) or "- none"
    return f"Verdict: {review.verdict}\n\nSummary: {review.summary}\n\nRisks:\n{risks}\n"
