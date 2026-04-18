from __future__ import annotations


from pathlib import Path


def slice_changed_files(
    changed_files: list[str],
    *,
    dependency_dag: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    changed = sorted(set(changed_files))
    if not dependency_dag:
        return {"changed_files": changed, "impacted_files": changed}

    impacted = set(changed)
    path_by_module = {_module_name_for_path(path): path for path in dependency_dag}
    changed_modules = {
        _module_name_for_path(path)
        for path in changed
        if path in dependency_dag
    }

    for path in changed:
        for imported in dependency_dag.get(path, []):
            target = path_by_module.get(imported)
            if target:
                impacted.add(target)

    for path, imports in dependency_dag.items():
        if any(imported in changed_modules for imported in imports):
            impacted.add(path)

    return {
        "changed_files": changed,
        "impacted_files": sorted(impacted),
    }


def _module_name_for_path(relative_path: str) -> str:
    path = Path(relative_path)
    if path.name == "__init__.py":
        return ".".join(path.parts[:-1])
    return ".".join(path.with_suffix("").parts)
