from __future__ import annotations

from .schema import EvidenceLedgerModel, VerificationStatus


def render_ledger(ledger: EvidenceLedgerModel) -> str:
    lines = [
        "--------------------------------------------------",
        "AXIOM - Evidence Ledger",
        "--------------------------------------------------",
        f"Bug:            {ledger.bug_summary}",
        f"Axiom:          {ledger.axiom.value}",
        f"Function:       {ledger.function_name}",
        "",
        "Patch:",
        f"  {ledger.patch_summary}",
        "",
        "Contracts:",
    ]
    lines.extend(f"  {contract}" for contract in ledger.contracts)
    lines.extend(["", f"Verification:   {ledger.verification.status.value}", ""])

    if ledger.verification.status == VerificationStatus.VERIFIED:
        lines.append(
            f"CrossHair:      {ledger.verification.raw_output or 'No counterexamples found.'}"
        )
        if ledger.tests is not None:
            lines.append(f"Tests:          {ledger.tests.passed}/{ledger.tests.passed + ledger.tests.failed} passing")
        lines.append("Status:         Verified under contracts")
    elif ledger.verification.status == VerificationStatus.FALSIFIED:
        lines.append("Counterexample:")
        lines.append(f"  {ledger.verification.counterexample or 'CrossHair found a witness'}")
        if ledger.verification.violated_condition:
            lines.append(f"Violated:       {ledger.verification.violated_condition}")
        lines.append("Status:         Patch rejected - counterexample found")
    else:
        if ledger.verification.timeout_seconds:
            lines.append(f"CrossHair:      timed out at {ledger.verification.timeout_seconds:.1f} seconds")
        else:
            lines.append("CrossHair:      analysis ended without a proof")
        if ledger.tests is not None:
            lines.append(f"Tests:          {ledger.tests.passed}/{ledger.tests.passed + ledger.tests.failed} passing")
        lines.append("Status:         Passed tests but unproven beyond them")

    lines.extend(
        [
            "",
            f"Wall time:      {ledger.wall_time_seconds:.2f}s",
            f"Final status:   {ledger.final_status.value}",
            "--------------------------------------------------",
        ]
    )
    return "\n".join(lines)
