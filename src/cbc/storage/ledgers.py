from __future__ import annotations

from pathlib import Path

from cbc.models import RunLedger
from cbc.storage.artifacts import write_json


def export_ledger_snapshot(path: Path, ledger: RunLedger) -> None:
    write_json(path, ledger.model_dump(mode="json"))
