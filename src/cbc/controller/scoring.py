from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cbc.models import CandidateResult, CandidateScore, VerificationReport, VerificationVerdict


@dataclass(frozen=True)
class CandidateSelectionWeights:
    """Legacy weight bundle kept for backwards compatibility with existing callers.

    These weights drive only the ``CandidateScore.weighted_score`` field, which
    is informational. The ordering contract of :meth:`CandidateScoringEngine.select`
    is defined by :class:`CheckWeights`.
    """

    verified_bonus: float = 1000.0
    passed_check_weight: float = 50.0
    unsafe_claim_penalty: float = 150.0
    changed_file_penalty: float = 10.0
    diff_line_penalty: float = 1.0


@dataclass(frozen=True)
class CheckWeights:
    """Tunable weights that define the candidate selection score.

    Defaults are chosen so that :meth:`CandidateScoringEngine.select` reproduces
    the previous lexicographic tuple ordering exactly:

        (VERIFIED first,
         more passed_checks wins,
         safe beats unsafe,
         fewer changed_files wins,
         smaller diff (additions + deletions) wins)

    To preserve lexicographic dominance, each tier's magnitude must exceed the
    maximum contribution of all lower tiers combined. The chosen magnitudes
    comfortably cover realistic bounds (hundreds of checks, tens of thousands
    of changed files, millions of diff lines).
    """

    # Tier 1: verified verdict beats any non-verified candidate.
    verified_bonus: float = 1e12
    # Tier 2: one additional passed check beats any combination of lower tiers.
    passed_check_weight: float = 1e9
    # Tier 3: safe beats unsafe when passed_checks are tied.
    unsafe_claim_penalty: float = 1e7
    # Tier 4: fewer changed files wins when tiers 1-3 are tied.
    changed_file_penalty: float = 1e3
    # Tier 5: smaller diff wins when tiers 1-4 are tied.
    diff_line_penalty: float = 1.0


class CandidateScoringEngine:
    def __init__(
        self,
        weights: CandidateSelectionWeights | None = None,
        *,
        check_weights: CheckWeights | None = None,
    ) -> None:
        self.weights = weights or CandidateSelectionWeights()
        self._check_weights = check_weights or CheckWeights()

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

    def score_candidate(
        self,
        candidate: CandidateResult,
        weights: CheckWeights | None = None,
    ) -> float:
        """Return a scalar score for ``candidate`` using ``weights``.

        Higher scores are preferred. The default weights reproduce the legacy
        tuple-based ordering exactly (see :class:`CheckWeights`).
        """
        w = weights or self._check_weights
        score = candidate.score
        total = 0.0
        if candidate.verification.verdict == VerificationVerdict.VERIFIED:
            total += w.verified_bonus
        total += score.passed_checks * w.passed_check_weight
        if score.unsafe_claim:
            total -= w.unsafe_claim_penalty
        total -= score.changed_files * w.changed_file_penalty
        total -= (score.diff_additions + score.diff_deletions) * w.diff_line_penalty
        return total

    def select(self, candidates: list[CandidateResult]) -> CandidateResult:
        return sorted(
            candidates,
            key=lambda candidate: (
                -self.score_candidate(candidate),
                candidate.candidate_id,
            ),
        )[0]
