from __future__ import annotations

from pathlib import Path

from axiom.cli import main


def test_bug_test_mode_works(capsys) -> None:
    exit_code = main(["--bug", "demo_repo/checkout/discount.py", "--test", "demo_repo/tests/test_discount.py"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "AXIOM - Evidence Ledger" in out


def test_stacktrace_function_mode_works(tmp_path: Path, capsys) -> None:
    stacktrace = tmp_path / "stacktrace.txt"
    stacktrace.write_text(
        "Traceback (most recent call last):\nAssertionError: apply_discount(100, 150) should not be negative\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--stacktrace",
            str(stacktrace),
            "--function",
            "demo_repo/checkout/discount.py",
        ]
    )
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "AXIOM - Evidence Ledger" in out


def test_invalid_arg_combinations_fail(capsys) -> None:
    exit_code = main(
        [
            "--stacktrace",
            "missing.txt",
            "--function",
            "demo_repo/checkout/discount.py",
            "--test",
            "demo_repo/tests/test_discount.py",
        ]
    )
    err = capsys.readouterr().err
    assert exit_code == 2
    assert "`--test` is only supported with `--bug` mode." in err


def test_missing_files_fail_cleanly(capsys) -> None:
    exit_code = main(["--stacktrace", "missing.txt", "--function", "demo_repo/checkout/discount.py"])
    err = capsys.readouterr().err
    assert exit_code == 2
    assert "Stacktrace file not found" in err
