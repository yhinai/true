"use client";

import Link from "next/link";
import { use, useMemo } from "react";
import { streamUrl } from "@/lib/api";
import { useSSE } from "@/lib/useSSE";

type Ledger = {
  run_id: string;
  task_id?: string;
  title?: string;
  mode?: string;
  verdict?: string;
  adapter?: string;
  started_at?: string;
  ended_at?: string;
  attempts?: unknown[];
  final_summary?: Record<string, unknown>;
  [key: string]: unknown;
};

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: runId } = use(params);
  const url = useMemo(() => streamUrl(runId), [runId]);
  const sse = useSSE<Ledger>(url);

  const ledger = sse.data;
  const verdict = (ledger?.verdict || "PENDING").toUpperCase();
  const terminal = sse.event === "done";
  const errored = sse.event === "error";

  return (
    <section>
      <div className="row">
        <Link href="/">← runs</Link>
        <h2 style={{ margin: 0 }}>{runId}</h2>
        <span className={`verdict ${verdict}`}>{verdict}</span>
        <span className={"dot " + (sse.connected && !terminal ? "live" : "")} />
        <span className="muted">
          {errored
            ? "error"
            : terminal
            ? "complete"
            : sse.connected
            ? "streaming"
            : "reconnecting…"}
        </span>
      </div>

      {!ledger ? (
        <div className="panel muted">Waiting for first SSE frame…</div>
      ) : (
        <>
          <div className="panel">
            <div className="row">
              <div>
                <div className="muted">task</div>
                <div>{ledger.task_id || "—"}</div>
              </div>
              <div>
                <div className="muted">mode</div>
                <div>{ledger.mode || "—"}</div>
              </div>
              <div>
                <div className="muted">adapter</div>
                <div>{ledger.adapter || "—"}</div>
              </div>
              <div>
                <div className="muted">started</div>
                <div>{ledger.started_at || "—"}</div>
              </div>
              <div>
                <div className="muted">ended</div>
                <div>{ledger.ended_at || "—"}</div>
              </div>
              <div>
                <div className="muted">attempts</div>
                <div>{Array.isArray(ledger.attempts) ? ledger.attempts.length : 0}</div>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <strong>Ledger</strong>
              <span className="muted">updates on every mtime change</span>
            </div>
            <pre className="ledger">{JSON.stringify(ledger, null, 2)}</pre>
          </div>
        </>
      )}
    </section>
  );
}
