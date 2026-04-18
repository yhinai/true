from axiom.pipeline import AxiomPipeline, PipelineInput
from axiom.patcher import PatchGenerator
from axiom.schema import PatchProposal, VerificationOutcome, VerificationStatus


def test_pipeline_produces_verified_status_for_demo_bug() -> None:
    ledger = AxiomPipeline().run(
        PipelineInput(
            bug_source_path="demo_repo/checkout/discount.py",
            test_path="demo_repo/tests/test_discount.py",
        )
    )
    assert ledger.final_status == VerificationStatus.VERIFIED
    assert ledger.tests is not None and ledger.tests.ok


def test_pipeline_can_force_unproven_path() -> None:
    ledger = AxiomPipeline().run(
        PipelineInput(
            bug_source_path="demo_repo/checkout/discount.py",
            test_path="demo_repo/tests/test_discount.py",
        ),
        force_unproven=True,
    )
    assert ledger.final_status == VerificationStatus.UNPROVEN


def test_pipeline_can_render_falsified_original_path() -> None:
    ledger = AxiomPipeline().run(
        PipelineInput(
            bug_source_path="demo_repo/checkout/discount.py",
            test_path="demo_repo/tests/test_discount.py",
            verify_original=True,
        )
    )
    assert ledger.final_status == VerificationStatus.FALSIFIED
    assert ledger.verification.counterexample is not None


def test_verify_original_skips_patch_generation() -> None:
    class FailingPatchGenerator(PatchGenerator):
        def propose_patch(self, *args, **kwargs):  # type: ignore[override]
            raise AssertionError("patch generation should not run during original verification")

    ledger = AxiomPipeline(patcher=FailingPatchGenerator()).run(
        PipelineInput(
            bug_source_path="demo_repo/checkout/discount.py",
            test_path="demo_repo/tests/test_discount.py",
            verify_original=True,
        )
    )
    assert ledger.final_status == VerificationStatus.FALSIFIED


def test_pipeline_uses_second_retry_before_giving_up() -> None:
    class RetryPatchGenerator(PatchGenerator):
        def __init__(self) -> None:
            super().__init__(model="test-model")
            self.calls = 0

        def propose_patch(self, classification, function_source, failing_context, counterexample=None):  # type: ignore[override]
            self.calls += 1
            return PatchProposal(
                function_name=classification.target_function,
                patched_source=f"def apply_discount(price: float, pct: int) -> float:\n    return {self.calls}\n",
                diff_summary=f"[+{self.calls} -0 lines]",
                changed_lines=self.calls,
                rationale=f"attempt {self.calls}",
            )

    class RetryVerifier:
        python_bin = ".venv/bin/python"
        timeout_seconds = 5.0

        def __init__(self) -> None:
            self.calls = 0

        def verify_source(self, source: str, function_name: str) -> VerificationOutcome:
            self.calls += 1
            if self.calls < 3:
                return VerificationOutcome(
                    status=VerificationStatus.FALSIFIED,
                    raw_output="counterexample",
                    command=["python", "-m", "crosshair"],
                    counterexample=f"{function_name}(price=0, pct={100 + self.calls})",
                    violated_condition="result >= 0",
                )
            return VerificationOutcome(
                status=VerificationStatus.VERIFIED,
                raw_output="No counterexamples found.",
                command=["python", "-m", "crosshair"],
            )

    patcher = RetryPatchGenerator()
    verifier = RetryVerifier()
    ledger = AxiomPipeline(patcher=patcher, verifier=verifier).run(
        PipelineInput(
            function_source="def apply_discount(price: float, pct: int) -> float:\n    return price\n",
            bug_text="apply_discount returned a negative result",
            run_tests=False,
        )
    )
    assert ledger.final_status == VerificationStatus.VERIFIED
    assert patcher.calls == 3
    assert verifier.calls == 3


def test_pipeline_reports_real_pytest_counts(tmp_path) -> None:
    package = tmp_path / "sample_pkg"
    package.mkdir()
    source_path = package / "discount.py"
    source_path.write_text(
        "def apply_discount(price: float, pct: int) -> float:\n    return price * (100 - pct) / 100\n",
        encoding="utf-8",
    )
    test_path = tmp_path / "test_discount.py"
    test_path.write_text(
        "from sample_pkg.discount import apply_discount\n\n"
        "def test_discount_bounds_low():\n"
        "    assert apply_discount(100, 0) == 100\n\n"
        "def test_discount_bounds_high():\n"
        "    assert apply_discount(100, 100) == 0\n",
        encoding="utf-8",
    )
    ledger = AxiomPipeline().run(
        PipelineInput(
            bug_source_path=str(source_path),
            test_path=str(test_path),
        )
    )
    assert ledger.tests is not None
    assert ledger.tests.passed == 2
    assert ledger.tests.failed == 0
