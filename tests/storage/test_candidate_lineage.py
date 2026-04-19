from pathlib import Path

from cbc.storage.candidate_lineage import (
    CandidateSnapshot,
    init_lineage_schema,
    insert_snapshot,
    list_snapshots_for_run,
)


def test_insert_and_list_snapshots(tmp_path: Path):
    db = tmp_path / "test.sqlite"
    init_lineage_schema(db)
    snap = CandidateSnapshot(
        snapshot_id="s-1",
        parent_id=None,
        run_id="r-1",
        candidate_index=0,
        verdict="VERIFIED",
    )
    insert_snapshot(db, snap)
    results = list_snapshots_for_run(db, "r-1")
    assert len(results) == 1
    assert results[0].snapshot_id == "s-1"
    assert results[0].parent_id is None


def test_lineage_parent_child(tmp_path: Path):
    db = tmp_path / "test.sqlite"
    init_lineage_schema(db)
    base = CandidateSnapshot(snapshot_id="base", parent_id=None, run_id="r-1", candidate_index=-1, verdict="UNPROVEN")
    child_a = CandidateSnapshot(snapshot_id="ca", parent_id="base", run_id="r-1", candidate_index=0, verdict="FALSIFIED")
    child_b = CandidateSnapshot(snapshot_id="cb", parent_id="base", run_id="r-1", candidate_index=1, verdict="VERIFIED")
    for s in (base, child_a, child_b):
        insert_snapshot(db, s)
    results = list_snapshots_for_run(db, "r-1")
    ids = sorted(s.snapshot_id for s in results)
    assert ids == ["base", "ca", "cb"]
    parents = {s.snapshot_id: s.parent_id for s in results}
    assert parents == {"base": None, "ca": "base", "cb": "base"}


def test_init_schema_is_idempotent(tmp_path: Path):
    db = tmp_path / "test.sqlite"
    init_lineage_schema(db)
    init_lineage_schema(db)  # must not raise
    snap = CandidateSnapshot(snapshot_id="s-1", parent_id=None, run_id="r-1", candidate_index=0, verdict="VERIFIED")
    insert_snapshot(db, snap)
    assert len(list_snapshots_for_run(db, "r-1")) == 1
