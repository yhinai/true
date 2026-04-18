from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class PropertyCheckResult:
    status: str
    engine: str
    runs: int
    failures: int
    message: str | None = None
    counterexample: dict[str, Any] | None = None
    artifact_path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "engine": self.engine,
            "runs": self.runs,
            "failures": self.failures,
            "message": self.message,
            "counterexample": self.counterexample,
            "artifact_path": self.artifact_path,
        }


def run_property_cases(
    property_check: Callable[[Any], Any],
    cases: Iterable[Any],
    *,
    checker_name: str = "property_check",
    artifact_dir: str | Path | None = None,
    artifact_name: str = "counterexample.json",
) -> PropertyCheckResult:
    runs = 0
    for case in cases:
        runs += 1
        try:
            result = property_check(case)
            if result is False:
                raise AssertionError("Property returned False.")
        except Exception as error:  # noqa: BLE001
            payload = _counterexample_payload(checker_name=checker_name, value=case, error=error)
            artifact_path = _maybe_write_counterexample(payload, artifact_dir=artifact_dir, artifact_name=artifact_name)
            return PropertyCheckResult(
                status="failed",
                engine="cases",
                runs=runs,
                failures=1,
                message=f"Property failed on case {runs}.",
                counterexample=payload,
                artifact_path=artifact_path,
            )

    return PropertyCheckResult(
        status="passed",
        engine="cases",
        runs=runs,
        failures=0,
        message="No counterexample found in supplied cases.",
    )


def run_hypothesis_property(
    strategy: Any,
    property_check: Callable[[Any], Any],
    *,
    checker_name: str = "hypothesis_property",
    max_examples: int = 100,
    seed: int | None = 1,
    artifact_dir: str | Path | None = None,
    artifact_name: str = "hypothesis_counterexample.json",
) -> PropertyCheckResult:
    try:
        import hypothesis
        from hypothesis import HealthCheck, given, settings
    except Exception:  # noqa: BLE001
        return PropertyCheckResult(
            status="unavailable",
            engine="hypothesis",
            runs=0,
            failures=0,
            message="Hypothesis is not installed.",
        )

    runs = 0
    observed_failure: dict[str, Any] = {}

    @settings(
        max_examples=max_examples,
        derandomize=True,
        deadline=None,
        database=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(strategy)
    def _generated_test(value: Any) -> None:
        nonlocal runs
        runs += 1
        try:
            result = property_check(value)
            if result is False:
                raise AssertionError("Property returned False.")
        except Exception as error:  # noqa: BLE001
            observed_failure.update(_counterexample_payload(checker_name=checker_name, value=value, error=error))
            raise

    wrapped = _generated_test
    if seed is not None:
        wrapped = hypothesis.seed(seed)(wrapped)

    try:
        wrapped()
    except Exception as error:  # noqa: BLE001
        if not observed_failure:
            observed_failure = _counterexample_payload(checker_name=checker_name, value="<unknown>", error=error)
        artifact_path = _maybe_write_counterexample(
            observed_failure,
            artifact_dir=artifact_dir,
            artifact_name=artifact_name,
        )
        return PropertyCheckResult(
            status="failed",
            engine="hypothesis",
            runs=runs,
            failures=1,
            message="Hypothesis found a counterexample.",
            counterexample=observed_failure,
            artifact_path=artifact_path,
        )

    return PropertyCheckResult(
        status="passed",
        engine="hypothesis",
        runs=runs,
        failures=0,
        message="No counterexample found by Hypothesis.",
    )


def _counterexample_payload(*, checker_name: str, value: Any, error: BaseException) -> dict[str, Any]:
    return {
        "checker": checker_name,
        "input": _json_safe(value),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _maybe_write_counterexample(
    payload: dict[str, Any],
    *,
    artifact_dir: str | Path | None,
    artifact_name: str,
) -> str | None:
    if artifact_dir is None:
        return None
    target_directory = Path(artifact_dir)
    target_directory.mkdir(parents=True, exist_ok=True)
    target_path = target_directory / artifact_name
    target_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(target_path)


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)
