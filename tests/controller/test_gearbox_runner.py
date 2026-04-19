import asyncio

import pytest

from cbc.controller.gearbox_runner import ParallelCandidateSpec, run_gearbox_parallel


@pytest.mark.asyncio
async def test_runs_candidates_in_parallel():
    call_order: list[str] = []

    def make_coder(idx: int):
        async def fake_coder():
            call_order.append(f"start-{idx}")
            await asyncio.sleep(0.05)
            call_order.append(f"end-{idx}")
            return f"cand-{idx}"
        return fake_coder

    async def fake_verify(cand: str) -> dict:
        return {"cand": cand, "verdict": "FALSIFIED" if cand.endswith("0") else "VERIFIED"}

    specs = [
        ParallelCandidateSpec(index=i, run_coder=make_coder(i), verify=fake_verify)
        for i in range(3)
    ]

    results = await run_gearbox_parallel(specs)

    # All three "start" events happen before any "end" event — real parallelism.
    assert call_order.index("end-0") > call_order.index("start-2")
    assert len(results) == 3
    assert {r["verdict"] for r in results} == {"FALSIFIED", "VERIFIED"}


@pytest.mark.asyncio
async def test_preserves_result_order():
    async def coder_for(idx: int):
        async def _c():
            await asyncio.sleep(0.01 * (3 - idx))  # idx 0 is slowest
            return idx
        return _c

    async def verify(cand: int) -> dict:
        return {"cand": cand}

    specs = [
        ParallelCandidateSpec(index=i, run_coder=await coder_for(i), verify=verify)
        for i in range(3)
    ]

    results = await run_gearbox_parallel(specs)

    # asyncio.gather preserves submission order
    assert [r["cand"] for r in results] == [0, 1, 2]


@pytest.mark.asyncio
async def test_empty_spec_list_returns_empty():
    assert await run_gearbox_parallel([]) == []
