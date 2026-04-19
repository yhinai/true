from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cbc.models import CandidateResult, CandidateScore, VerificationReport, VerificationVerdict


@dataclass(frozen=True)
class CandidateSelectionWeights:
    verified_bonus: float = 1000.0
    passed_check_weight: float = 50.0
    unsafe_claim_penalty: float = 150.0
    changed_file_penalty: float = 10.0
    diff_line_penalty: float = 1.0


class CandidateScoringEngine:
    def __init__(self, weights: CandidateSelectionWeights | None = None) -> None:
        self.weights = weights or CandidateSelectionWeights()

    def score(self, verification: VerificationReport, diff_summary: dict[str, Any]) -> CandidateScore:
        passed_checks = sum(1 for check in verification.checks if check.status.value == "passed")
        additions = 0
        deletions = 0
        for item in diff_summary.get("files", []):
            if isinstance(item, dict):
                additions += int(item.get("additions", 0))
                deletions += int(item.get("deletions", 0))
        weighted_score = (
            (self.weights.verified_bonus if verification.verdict == VerificationVerdict.VERIFIED else 0.0)
            + (passed_checks * self.weights.passed_check_weight)
            - (self.weights.unsafe_claim_penalty if verification.unsafe_claim_detected else 0.0)
            - (len(verification.changed_files) * self.weights.changed_file_penalty)
            - ((additions + deletions) * self.weights.diff_line_penalty)
        )
        return CandidateScore(
            passed_checks=passed_checks,
            unsafe_claim=verification.unsafe_claim_detected,
            changed_files=len(verification.changed_files),
            diff_additions=additions,
            diff_deletions=deletions,
            weighted_score=weighted_score,
        )

    def select(self, candidates: list[CandidateResult]) -> CandidateResult:
        return sorted(
            candidates,
            key=lambda candidate: (
                0 if candidate.verification.verdict == VerificationVerdict.VERIFIED else 1,
                -candidate.score.passed_checks,
                1 if candidate.score.unsafe_claim else 0,
                candidate.score.changed_files,
                candidate.score.diff_additions + candidate.score.diff_deletions,
                candidate.candidate_id,
            ),
        )[0]
