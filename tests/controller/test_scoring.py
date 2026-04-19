from __future__ import annotations

from pathlib import Path

import pytest

from cbc.controller.scoring import CandidateScoringEngine, CheckWeights
from cbc.models import (
    CandidateResult,
    CandidateScore,
    CheckResult,
    CheckStatus,
    ModelResponse,
    VerificationReport,
    VerificationVerdict,
)


def _make_candidate(
    candidate_id: str,
    *,
    verdict: VerificationVerdict,
    passed_checks: int,
    unsafe_claim: bool = False,
    changed_files: int = 0,
    diff_additions: int = 0,
    diff_deletions: int = 0,
) -> CandidateResult:
    checks = [
        CheckResult(name=f"check_{i}", command="noop", status=CheckStatus.PASSED)
        for i in range(passed_checks)
    ]
    verification = VerificationReport(
        verdict=verdict,
        checks=checks,
        summary="test",
        unsafe_claim_detected=unsafe_claim,
        changed_files=[f"file_{i}.py" for i in range(changed_files)],
    )
    return CandidateResult(
        candidate_id=candidate_id,
        candidate_role="primary" if candidate_id.endswith("a") else "alternate",
        attempt=1,
        prompt="p",
        model_response=ModelResponse(summary="s"),
        verification=verification,
        workspace_dir=Path("/tmp"),
        diff_summary={},
        score=CandidateScore(
            passed_checks=passed_checks,
            unsafe_claim=unsafe_claim,
            changed_files=changed_files,
            diff_additions=diff_additions,
            diff_deletions=diff_deletions,
        ),
    )


def _legacy_select(candidates: list[CandidateResult]) -> CandidateResult:
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


@pytest.fixture
def engine() -> CandidateScoringEngine:
    return CandidateScoringEngine()


@pytest.mark.parametrize(
    "scenario",
    [
        # Verified beats non-verified regardless of checks.
        [
            dict(candidate_id="candidate_a", verdict=VerificationVerdict.UNPROVEN, passed_checks=10),
            dict(candidate_id="candidate_b", verdict=VerificationVerdict.VERIFIED, passed_checks=1),
        ],
        # Among verified, more passed checks wins.
        [
            dict(candidate_id="candidate_a", verdict=VerificationVerdict.VERIFIED, passed_checks=2),
            dict(candidate_id="candidate_b", verdict=VerificationVerdict.VERIFIED, passed_checks=5),
        ],
        # Safe beats unsafe when checks are tied.
        [
            dict(candidate_id="candidate_a", verdict=VerificationVerdict.VERIFIED, passed_checks=3, unsafe_claim=True),
            dict(candidate_id="candidate_b", verdict=VerificationVerdict.VERIFIED, passed_checks=3, unsafe_claim=False),
        ],
        # Fewer changed files wins when earlier tiers tied.
        [
            dict(candidate_id="candidate_a", verdict=VerificationVerdict.VERIFIED, passed_checks=3, changed_files=5),
            dict(candidate_id="candidate_b", verdict=VerificationVerdict.VERIFIED, passed_checks=3, changed_files=2),
        ],
        # Smaller diff wins when earlier tiers tied.
        [
            dict(candidate_id="candidate_a", verdict=VerificationVerdict.VERIFIED, passed_checks=3, changed_files=2, diff_additions=80, diff_deletions=20),
            dict(candidate_id="candidate_b", verdict=VerificationVerdict.VERIFIED, passed_checks=3, changed_files=2, diff_additions=5, diff_deletions=5),
        ],
        # Lexicographic candidate_id is the final tie-break.
        [
            dict(candidate_id="candidate_b", verdict=VerificationVerdict.VERIFIED, passed_checks=3),
            dict(candidate_id="candidate_a", verdict=VerificationVerdict.VERIFIED, passed_checks=3),
        ],
        # Three-way: one verified-unsafe, one verified-safe-fewer-checks, one unproven.
        [
            dict(candidate_id="candidate_a", verdict=VerificationVerdict.VERIFIED, passed_checks=5, unsafe_claim=True),
            dict(candidate_id="candidate_b", verdict=VerificationVerdict.VERIFIED, passed_checks=4, unsafe_claim=False),
            dict(candidate_id="candidate_c", verdict=VerificationVerdict.UNPROVEN, passed_checks=10),
        ],
    ],
)
def test_weighted_select_matches_legacy_winner(
    engine: CandidateScoringEngine, scenario: list[dict]
) -> None:
    candidates = [_make_candidate(**spec) for spec in scenario]
    assert engine.select(candidates).candidate_id == _legacy_select(candidates).candidate_id


def test_score_candidate_verified_dominates() -> None:
    engine = CandidateScoringEngine()
    verified = _make_candidate("candidate_a", verdict=VerificationVerdict.VERIFIED, passed_checks=0)
    unproven_many_checks = _make_candidate(
        "candidate_b", verdict=VerificationVerdict.UNPROVEN, passed_checks=500
    )
    assert engine.score_candidate(verified) > engine.score_candidate(unproven_many_checks)


def test_score_candidate_accepts_custom_weights() -> None:
    engine = CandidateScoringEngine()
    candidate = _make_candidate(
        "candidate_a",
        verdict=VerificationVerdict.VERIFIED,
        passed_checks=2,
        changed_files=3,
        diff_additions=4,
        diff_deletions=1,
    )
    custom = CheckWeights(
        verified_bonus=1.0,
        passed_check_weight=1.0,
        unsafe_claim_penalty=0.0,
        changed_file_penalty=0.0,
        diff_line_penalty=0.0,
    )
    # Only verified_bonus (1) + 2 * passed_check_weight (2) = 3.0
    assert engine.score_candidate(candidate, custom) == pytest.approx(3.0)


def test_constructor_accepts_check_weights() -> None:
    custom = CheckWeights(passed_check_weight=0.0, verified_bonus=0.0)
    engine = CandidateScoringEngine(check_weights=custom)
    candidate = _make_candidate(
        "candidate_a", verdict=VerificationVerdict.VERIFIED, passed_checks=3
    )
    # With both weights zeroed out, score should be 0 minus any penalties (none here).
    assert engine.score_candidate(candidate) == pytest.approx(0.0)
