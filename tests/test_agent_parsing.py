from __future__ import annotations

from pathlib import Path

from axiom.prompt_parser import GUIDANCE, load_prompt_paths, parse_prompt


def test_parse_pasted_code_and_failing_test() -> None:
    prompt = """
```python
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
```

```text
def test_apply_discount_rejects_percentages_above_100():
    with pytest.raises(ValueError):
        apply_discount(100, 150)
```
"""
    parsed = parse_prompt(prompt)
    assert parsed.function_source is not None
    assert "def apply_discount" in parsed.function_source
    assert parsed.error_info is not None
    assert "pytest.raises" in parsed.error_info
    assert parsed.source_mode == "pasted_function_and_test"


def test_parse_pasted_code_and_text_fence_stacktrace() -> None:
    prompt = """
```python
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
```

```text
Traceback (most recent call last):
AssertionError: result should never be negative
```
"""
    parsed = parse_prompt(prompt)
    assert parsed.function_source is not None
    assert parsed.error_info is not None
    assert "Traceback" in parsed.error_info
    assert parsed.source_mode == "pasted_function_and_stacktrace"


def test_parse_pasted_code_and_stacktrace() -> None:
    prompt = """
```python
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
```

Traceback (most recent call last):
AssertionError: result should never be negative
"""
    parsed = parse_prompt(prompt)
    assert parsed.function_source is not None
    assert parsed.error_info is not None
    assert "Traceback" in parsed.error_info
    assert parsed.source_mode == "pasted_function_and_stacktrace"


def test_parse_bug_report_and_code() -> None:
    prompt = """
The discount function should reject percentages above 100 because the result can become negative.

```python
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
```
"""
    parsed = parse_prompt(prompt)
    assert parsed.function_source is not None
    assert parsed.context is not None
    assert "reject percentages above 100" in parsed.context
    assert parsed.source_mode == "pasted_bug_report_and_function"


def test_path_mode_still_works(tmp_path: Path) -> None:
    bug = tmp_path / "discount.py"
    bug.write_text("def apply_discount(price: float, pct: int) -> float:\n    return price * (100 - pct) / 100\n", encoding="utf-8")
    test = tmp_path / "test_discount.py"
    test.write_text("assert True\n", encoding="utf-8")
    parsed = load_prompt_paths(parse_prompt(f"bug={bug}\ntest={test}\n"))
    assert parsed.bug_path == str(bug)
    assert parsed.test_path == str(test)
    assert parsed.source_mode == "paths"


def test_path_mode_supports_function_and_stacktrace(tmp_path: Path) -> None:
    function_path = tmp_path / "discount.py"
    function_path.write_text(
        "def apply_discount(price: float, pct: int) -> float:\n    return price * (100 - pct) / 100\n",
        encoding="utf-8",
    )
    stacktrace_path = tmp_path / "stacktrace.txt"
    stacktrace_path.write_text(
        "Traceback (most recent call last):\nAssertionError: negative result\n",
        encoding="utf-8",
    )
    parsed = load_prompt_paths(parse_prompt(f"function={function_path}\nstacktrace={stacktrace_path}\n"))
    assert parsed.function_path == str(function_path)
    assert parsed.function_source is not None
    assert parsed.error_info is not None
    assert "Traceback" in parsed.error_info
    assert parsed.source_mode == "paths"


def test_bug_report_with_test_name_stays_bug_report_context() -> None:
    prompt = """
The issue shows up in test_apply_discount_rejects_percentages_above_100 and should reject percentages above 100.

```python
def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
```
"""
    parsed = parse_prompt(prompt)
    assert parsed.context is not None
    assert parsed.error_info is None
    assert parsed.source_mode == "pasted_bug_report_and_function"


def test_parse_async_function_prompt() -> None:
    prompt = """
```python
async def apply_discount(price: float, pct: int) -> float:
    return price * (100 - pct) / 100
```

Traceback (most recent call last):
AssertionError: result should never be negative
"""
    parsed = parse_prompt(prompt)
    assert parsed.function_source is not None
    assert "async def apply_discount" in parsed.function_source
    assert parsed.source_mode == "pasted_function_and_stacktrace"


def test_path_mode_rejects_ambiguous_combinations() -> None:
    try:
        parse_prompt("bug=/tmp/a.py\nstacktrace=/tmp/b.txt\n")
    except ValueError as exc:
        assert "only supports" in str(exc)
    else:
        raise AssertionError("expected ambiguous path mode to be rejected")


def test_path_mode_rejects_empty_stacktrace(tmp_path: Path) -> None:
    function_path = tmp_path / "discount.py"
    function_path.write_text(
        "def apply_discount(price: float, pct: int) -> float:\n    return price * (100 - pct) / 100\n",
        encoding="utf-8",
    )
    stacktrace_path = tmp_path / "stacktrace.txt"
    stacktrace_path.write_text("", encoding="utf-8")
    try:
        load_prompt_paths(parse_prompt(f"function={function_path}\nstacktrace={stacktrace_path}\n"))
    except ValueError as exc:
        assert "Stacktrace file is empty" in str(exc)
    else:
        raise AssertionError("expected empty stacktrace to be rejected")


def test_malformed_prompt_requires_guidance() -> None:
    parsed = parse_prompt("Please help.")
    assert not parsed.is_actionable
    assert "function code + failing test" in GUIDANCE
