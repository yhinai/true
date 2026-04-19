"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchRuns, runsStreamUrl, type RunSummary } from "@/lib/api";
import { getSupabase, type CbcRunRow } from "@/lib/supabase";
import { useSSE } from "@/lib/useSSE";

type Source = "sse" | "supabase" | "rest" | "empty";

export default function RunsIndexPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [source, setSource] = useState<Source>("empty");

  // 1) Try the live SSE feed from the FastAPI control plane.
  const sse = useSSE<RunSummary[]>(runsStreamUrl(), ["runs"]);
  useEffect(() => {
    if (sse.data) {
      setRuns(sse.data);
      setSource("sse");
    }
  }, [sse.data]);

  // 2) REST fallback (if SSE is unreachable, e.g. deployed frontend + no API).
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
      .catch(() => {
        /* fall through to Supabase */
      });
    return () => {
      cancelled = true;
    };
  }, [sse.connected, sse.data]);

  // 3) Supabase fallback: read the ledger mirror directly.
  useEffect(() => {
    if (runs.length > 0) return;
    const sb = getSupabase();
    if (!sb) return;
    let cancelled = false;
    (async () => {
      const { data, error } = await sb
        .from("cbc_runs")
        .select("run_id, task_id, verdict, started_at")
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

  return (
    <section>
      <div className="row">
        <h2 style={{ margin: 0 }}>Runs</h2>
        <span className={"dot " + (sse.connected ? "live" : "")} />
        <span className="muted">
          {sse.connected ? "live (SSE)" : source === "supabase" ? "supabase mirror" : source === "rest" ? "REST snapshot" : "disconnected"}
        </span>
      </div>

      {runs.length === 0 ? (
        <div className="panel muted">
          No runs yet. Start the API with <code>uv run cbc-api</code> and run{" "}
          <code>uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml</code>.
        </div>
      ) : (
        <div className="panel">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Task</th>
                <th>Verdict</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => {
                const verdict = (r.verification_state || r.merge_gate_verdict || "UNKNOWN").toUpperCase();
                return (
                  <tr key={r.run_id}>
                    <td>
                      <Link href={`/runs/${r.run_id}`}>{r.run_id}</Link>
                    </td>
                    <td>{r.task_id ?? "—"}</td>
                    <td>
                      <span className={`verdict ${verdict}`}>{verdict}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
