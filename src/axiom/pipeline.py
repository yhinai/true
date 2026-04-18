from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
import re
import tempfile

from .contracts import ContractGenerator
from .detector import BugDetector
from .ledger import render_ledger
from .patcher import PatchGenerator
from .schema import EvidenceLedgerModel, PatchProposal, TestRunResult, VerificationStatus
from .utils import read_text
from .verifier import CrossHairVerifier


@dataclass
class PipelineInput:
    bug_source_path: str | None = None
    function_source: str | None = None
    test_path: str | None = None
    bug_text: str | None = None
    run_tests: bool = True
    verify_original: bool = False


class AxiomPipeline:
    def __init__(
        self,
        detector: BugDetector | None = None,
        patcher: PatchGenerator | None = None,
        contracts: ContractGenerator | None = None,
        verifier: CrossHairVerifier | None = None,
        max_retries: int = 2,
    ) -> None:
        self.detector = detector or BugDetector()
        self.patcher = patcher or PatchGenerator()
        self.contracts = contracts or ContractGenerator()
        self.verifier = verifier or CrossHairVerifier()
        self.max_retries = max_retries

    def run(self, pipeline_input: PipelineInput, force_unproven: bool = False) -> EvidenceLedgerModel:
        started = time.perf_counter()
        original_source = self._resolve_function_source(pipeline_input)
        bug_text = self._resolve_bug_text(pipeline_input)

        classification = self.detector.classify(bug_text, original_source)
        if pipeline_input.verify_original:
            patch = PatchProposal(
                function_name=classification.target_function,
                patched_source=original_source,
                diff_summary="[+0 -0 lines]",
                changed_lines=0,
                rationale="Verification requested against the original buggy source.",
            )
        else:
            patch = self.patcher.propose_patch(classification, original_source, bug_text)
        contract_proposal = self.contracts.derive(classification, patch.patched_source)
        if pipeline_input.verify_original:
            contract_proposal.decorators = [
                "@icontract.require(lambda price: math.isfinite(price) and price >= 0)",
                "@icontract.ensure(lambda result: math.isfinite(result) and result >= 0)",
            ]
            contract_proposal.contract_block = "\n".join(contract_proposal.decorators)
            contract_proposal.rationale = "Original-source verification keeps the output safety goal but omits the patched percentage bound."
        verification = self._verify_patch(classification, patch, contract_proposal)

        if not pipeline_input.verify_original:
            retry_count = 0
            while verification.status == VerificationStatus.FALSIFIED and retry_count < self.max_retries:
                retry_count += 1
                patch = self.patcher.propose_patch(
                    classification,
                    original_source,
                    bug_text,
                    counterexample=verification.counterexample,
                )
                contract_proposal = self.contracts.derive(classification, patch.patched_source)
                verification = self._verify_patch(classification, patch, contract_proposal)

        if force_unproven:
            verification.status = VerificationStatus.UNPROVEN
            verification.timeout_seconds = verification.timeout_seconds or self.verifier.timeout_seconds

        test_result = None
        if pipeline_input.run_tests and pipeline_input.test_path and pipeline_input.bug_source_path:
            test_result = self._run_tests(
                patch.patched_source,
                pipeline_input.bug_source_path,
                pipeline_input.test_path,
            )

        wall_time = time.perf_counter() - started
        return EvidenceLedgerModel(
            bug_summary=classification.bug_summary,
            axiom=classification.axiom,
            function_name=classification.target_function,
            patch_summary=patch.diff_summary,
            patched_source=patch.patched_source,
            contracts=contract_proposal.decorators,
            verification=verification,
            tests=test_result,
            wall_time_seconds=wall_time,
            final_status=verification.status,
        )

    def _verify_patch(
        self,
        classification,
        patch: PatchProposal,
        contract_proposal,
    ):
        verifiable_source = self.contracts.apply_contracts(
            patch.patched_source,
            classification.target_function,
            contract_proposal.decorators,
        )
        return self.verifier.verify_source(verifiable_source, classification.target_function)

    def run_and_render(self, pipeline_input: PipelineInput, force_unproven: bool = False) -> str:
        return render_ledger(self.run(pipeline_input, force_unproven=force_unproven))

    def _resolve_function_source(self, pipeline_input: PipelineInput) -> str:
        if pipeline_input.function_source:
            return pipeline_input.function_source
        if pipeline_input.bug_source_path:
            return read_text(pipeline_input.bug_source_path)
        raise ValueError("Axiom requires either `bug_source_path` or `function_source`.")

    def _resolve_bug_text(self, pipeline_input: PipelineInput) -> str:
        if pipeline_input.bug_text:
            return pipeline_input.bug_text
        if pipeline_input.test_path:
            return read_text(pipeline_input.test_path)
        return ""

    def _run_tests(self, patched_source: str, bug_source_path: str, test_path: str) -> TestRunResult:
        source_path = Path(bug_source_path).resolve()
        test_file_path = Path(test_path).resolve()
        with tempfile.TemporaryDirectory() as tmpdir:
            staged_root = Path(tmpdir)
            staged_source_path, staged_test_path = self._stage_test_environment(
                staged_root,
                source_path,
                test_file_path,
            )
            staged_source_path.write_text(patched_source, encoding="utf-8")
            command = [self.verifier.python_bin, "-m", "pytest", str(staged_test_path), "-q"]
            env = os.environ.copy()
            env["PYTHONPATH"] = os.pathsep.join(
                value for value in [str(staged_root), env.get("PYTHONPATH", "")] if value
            )
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                cwd=staged_root,
                env=env,
            )

        output = "\n".join(part for part in [proc.stdout, proc.stderr] if part).strip()
        passed, failed = self._parse_pytest_counts(output, proc.returncode)
        return TestRunResult(
            command=command,
            passed=passed,
            failed=failed,
            ok=proc.returncode == 0,
            output=output,
        )

    @staticmethod
    def _parse_pytest_counts(output: str, returncode: int) -> tuple[int, int]:
        passed_match = re.search(r"(\d+)\s+passed", output)
        failed_match = re.search(r"(\d+)\s+failed", output)
        passed = int(passed_match.group(1)) if passed_match else (1 if returncode == 0 else 0)
        failed = int(failed_match.group(1)) if failed_match else 0
        return passed, failed

    @staticmethod
    def _stage_test_environment(
        staged_root: Path,
        source_path: Path,
        test_path: Path,
    ) -> tuple[Path, Path]:
        cwd = Path.cwd().resolve()
        if source_path.is_relative_to(cwd) and test_path.is_relative_to(cwd):
            relative_source = source_path.relative_to(cwd)
            relative_test = test_path.relative_to(cwd)
            top_level_entries = {relative_source.parts[0], relative_test.parts[0]}
            for entry in top_level_entries:
                origin = cwd / entry
                destination = staged_root / entry
                if origin.is_dir():
                    shutil.copytree(origin, destination, dirs_exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(origin, destination)
            return staged_root / relative_source, staged_root / relative_test

        common_root = Path(os.path.commonpath([str(source_path.parent), str(test_path.parent)])).resolve()
        shutil.copytree(common_root, staged_root, dirs_exist_ok=True)
        return staged_root / source_path.relative_to(common_root), staged_root / test_path.relative_to(common_root)
