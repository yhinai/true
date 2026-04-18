from __future__ import annotations


def slice_changed_files(changed_files: list[str]) -> dict[str, list[str]]:
    return {"changed_files": sorted(changed_files)}
