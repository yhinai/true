from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FailureModeEntry:
    mode: str
    message: str
    location: str | None = None
    artifact_path: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    created_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "message": self.message,
            "location": self.location,
            "artifact_path": self.artifact_path,
            "evidence": _json_safe(self.evidence),
            "created_at_utc": self.created_at_utc,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FailureModeEntry":
        return cls(
            mode=str(payload.get("mode", "unknown")),
            message=str(payload.get("message", "")),
            location=payload.get("location"),
            artifact_path=payload.get("artifact_path"),
            evidence=dict(payload.get("evidence", {})),
            created_at_utc=str(payload.get("created_at_utc", datetime.now(timezone.utc).isoformat())),
        )


@dataclass
class FailureModeLedger:
    entries: list[FailureModeEntry] = field(default_factory=list)

    def add(self, entry: FailureModeEntry) -> None:
        self.entries.append(entry)

    def record(
        self,
        mode: str,
        message: str,
        *,
        location: str | None = None,
        artifact_path: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> FailureModeEntry:
        entry = FailureModeEntry(
            mode=mode,
            message=message,
            location=location,
            artifact_path=artifact_path,
            evidence=evidence or {},
        )
        self.add(entry)
        return entry

    def to_dict(self) -> dict[str, Any]:
        return {"entries": [entry.as_dict() for entry in self.entries]}

    def counts_by_mode(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry.mode] = counts.get(entry.mode, 0) + 1
        return counts

    def save_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output_path

    @classmethod
    def load_json(cls, path: str | Path) -> "FailureModeLedger":
        input_path = Path(path)
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        entries = [FailureModeEntry.from_dict(item) for item in payload.get("entries", [])]
        return cls(entries=entries)


def record_exception(
    ledger: FailureModeLedger,
    error: BaseException,
    *,
    location: str | None = None,
    artifact_path: str | None = None,
    mode: str = "exception",
    evidence: dict[str, Any] | None = None,
) -> FailureModeEntry:
    payload: dict[str, Any] = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    if evidence:
        payload.update(evidence)
    return ledger.record(
        mode=mode,
        message=str(error),
        location=location,
        artifact_path=artifact_path,
        evidence=payload,
    )


def record_counterexample(
    ledger: FailureModeLedger,
    *,
    checker: str,
    input_value: Any,
    message: str = "Counterexample discovered.",
    artifact_path: str | None = None,
) -> FailureModeEntry:
    return ledger.record(
        mode="counterexample",
        message=message,
        artifact_path=artifact_path,
        evidence={"checker": checker, "input": _json_safe(input_value)},
    )


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)
