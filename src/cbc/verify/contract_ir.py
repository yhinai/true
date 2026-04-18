from __future__ import annotations

from pathlib import Path


def build_contract_graph(workspace: Path) -> list[str]:
    return [f"workspace:{workspace.name}"]
