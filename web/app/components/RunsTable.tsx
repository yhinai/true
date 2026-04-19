"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchRuns, runsStreamUrl, type RunSummary } from "@/lib/api";
import { getSupabase, type CbcRunRow } from "@/lib/supabase";
import { useSSE } from "@/lib/useSSE";

type Source = "sse" | "supabase" | "rest" | "empty";

export function RunsTable() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [source, setSource] = useState<Source>("empty");

  const sse = useSSE<RunSummary[]>(runsStreamUrl(), ["runs"]);
  useEffect(() => {
    if (sse.data) {
      setRuns(sse.data);
      setSource("sse");
    }
  }, [sse.data]);

  useEffect(() => {
    if (sse.connected || sse.data) return;
    let cancelled = false;
    fetchRuns()
      .then((r) => {
        if (!cancelled) {
          setRuns(r);
          setSource(r.length ? "rest" : "empty");
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [sse.connected, sse.data]);

  useEffect(() => {
    if (runs.length > 0) return;
    const sb = getSupabase();
    if (!sb) return;
    let cancelled = false;
    (async () => {
      const { data, error } = await sb
        .from("cbc_runs")
        .select("run_id, task_id, verdict, started_at, mode, adapter")
        .order("started_at", { ascending: false })
        .limit(50);
      if (!error && !cancelled && data) {
        const mapped: RunSummary[] = (data as CbcRunRow[]).map((r) => ({
          run_id: r.run_id,
          task_id: r.task_id ?? undefined,
          verification_state: r.verdict ?? undefined,
          merge_gate_verdict: r.verdict ?? undefined,
        }));
        setRuns(mapped);
        if (mapped.length) setSource("supabase");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [runs.length]);

  const sourceLabel =
    source === "sse"
      ? "LIVE SSE"
      : source === "rest"
      ? "REST SNAPSHOT"
      : source === "supabase"
      ? "SUPABASE MIRROR"
      : "AWAITING SIGNAL";

  return (
    <div className="panel">
      <div className="panel-head">
        <strong>Runs · ledger tail</strong>
        <span>
          <span className={`dot ${sse.connected ? "live" : "amber"}`} style={{ marginRight: 8 }} />
          {sourceLabel}
        </span>
      </div>

      {runs.length === 0 ? (
        <div className="event-empty">
          No runs in ledger yet. Kick one off with
          <br />
          <code style={{ color: "var(--amber)", marginTop: 10, display: "inline-block" }}>
            uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml
          </code>
        </div>
      ) : (
        <table className="runs">
          <thead>
            <tr>
              <th style={{ width: "34%" }}>Run</th>
              <th>Task</th>
              <th style={{ textAlign: "right" }}>Verdict</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => {
              const verdict = (r.verification_state || r.merge_gate_verdict || "UNKNOWN").toUpperCase();
              return (
                <tr key={r.run_id}>
                  <td className="run-id">
                    <Link href={`/runs/${r.run_id}`}>{r.run_id.slice(0, 16)}</Link>
                  </td>
                  <td>{r.task_id ?? "—"}</td>
                  <td style={{ textAlign: "right" }}>
                    <span className={`verdict ${verdict}`}>{verdict}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
