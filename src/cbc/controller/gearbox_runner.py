"""Parallel candidate execution for the gearbox controller."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass
class ParallelCandidateSpec:
    index: int
    run_coder: Callable[[], Awaitable[Any]]
    verify: Callable[[Any], Awaitable[dict]]


async def _run_one(spec: ParallelCandidateSpec) -> dict:
    candidate = await spec.run_coder()
    return await spec.verify(candidate)


async def run_gearbox_parallel(specs: list[ParallelCandidateSpec]) -> list[dict]:
    if not specs:
        return []
    return await asyncio.gather(*(_run_one(s) for s in specs))
