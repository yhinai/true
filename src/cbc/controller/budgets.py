from __future__ import annotations


def normalize_max_attempts(task_budget: int, default_budget: int, mode: str) -> int:
    if mode == "baseline":
        return 1
    return max(task_budget, default_budget, 1)
