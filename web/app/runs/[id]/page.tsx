"use client";

import Link from "next/link";
import { use, useEffect, useMemo, useState } from "react";
import { fetchRunReview, streamUrl, type RunReview } from "@/lib/api";
import { fetchLedgerFromSupabase } from "@/lib/supabase";
import { useSSE } from "@/lib/useSSE";

type Check = {
  name?: string;
  status?: string;
  duration_seconds?: number;
};

type Verification = {
  verdict?: string;
  summary?: string;
  checks?: Check[];
  changed_files?: string[];
  failure_mode_ledger?: string[];
  counterexample?: string | Record<string, unknown> | null;
};

type Attempt = {
  attempt: number;
  candidate_id?: string | null;
  candidate_role?: string | null;
  adapter_failure_reason?: string | null;
  model_response?: {
    summary?: string;
    claimed_success?: boolean;
  };
  verification?: Verification;
};

type Ledger = {
  run_id: string;
  task_id?: string;
  title?: string;
  mode?: string;
  controller_mode?: string;
  verdict?: string;
  adapter?: string;
  started_at?: string;
  ended_at?: string;
  model_calls_used?: number;
  total_tokens?: number;
  estimated_cost_usd?: number | null;
  unsafe_claims?: number;
  selected_candidate_id?: string | null;
  final_summary?: string;
  attempts?: Attempt[];
};

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: runId } = use(params);
  const url = useMemo(() => streamUrl(runId), [runId]);
  const sse = useSSE<Ledger>(url);
  const [fallback, setFallback] = useState<RunReview | null>(null);
  const [mirror, setMirror] = useState<Ledger | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchRunReview(runId)
      .then((payload) => {
        if (!cancelled) setFallback(payload);
      })
      .catch(() => {
        if (!cancelled) setFallback(null);
      });
    fetchLedgerFromSupabase(runId)
      .then((payload) => {
        if (!cancelled && payload) setMirror(payload as unknown as Ledger);
      })
      .catch(() => {
        if (!cancelled) setMirror(null);
      });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  const ledger = sse.data ?? mirror;
  const attempts = ledger?.attempts ?? [];
  const latest = attempts[attempts.length - 1];
  const fallbackChecks = fallback?.summary?.verification?.checks ?? [];
  const fallbackFiles = fallback?.summary?.diff?.files ?? [];
  const verdict = (
    ledger?.verdict
    || fallback?.summary?.verification?.state
    || fallback?.summary?.merge_gate?.verdict
    || "PENDING"
  ).toUpperCase();
  const terminal = sse.event === "done";
  const errored = sse.event === "error";
  const fromMirror = !sse.data && !!mirror;
  const streamState = fromMirror
    ? "MIRROR"
    : errored
    ? "ERROR"
    : terminal
    ? "COMPLETE"
    : sse.connected
    ? "STREAMING"
    : "RECONNECTING";

  return (
    <>
      <div className="run-hero">
        <Link className="back" href="/#runs">
          ← back to runs
        </Link>
        <div>
          <div className="run-kicker">Run ledger</div>
          <h1>{ledger?.title || ledger?.task_id || fallback?.task_id || runId}</h1>
          <div className="run-subtitle">{runId}</div>
        </div>
        <div className="run-badges">
          <span className={`verdict ${verdict}`}>{verdict}</span>
          <span className="run-stream-badge">
            <span
              className={`dot ${
                sse.connected && !terminal
                  ? "live"
                  : fromMirror
                  ? "mirror"
                  : "amber"
              }`}
            />
            {streamState}
          </span>
        </div>
      </div>

      {!ledger ? (
        <>
          <div className="meta-grid">
            <Meta label="Task" value={fallback?.task_id} />
            <Meta label="Mode" value={fallback?.summary?.merge_gate?.verdict ? "review snapshot" : "—"} />
            <Meta label="Controller" value="—" />
            <Meta label="Attempts" value="—" />
            <Meta label="Unsafe claims" value={String(fallback?.summary?.verification?.unsafe_claims ?? "—")} />
            <Meta label="Model calls" value="—" />
            <Meta label="Selected candidate" value="—" />
            <Meta label="Started" value="—" />
            <Meta label="Ended" value="—" />
            <Meta label="Tokens" value="—" />
            <Meta label="Est. cost" value="—" />
          </div>

          <div className="run-layout">
            <div className="panel run-summary-panel">
              <div className="panel-head">
                <strong>Historical snapshot</strong>
                <span>REST FALLBACK</span>
              </div>
              <div className="run-summary-copy">
                {fallback?.summary?.merge_gate?.reason
                  || "Waiting for the live ledger stream to hydrate this page."}
              </div>
              {fallbackChecks.length > 0 && (
                <div className="failure-chip-row">
                  {fallbackChecks.slice(0, 6).map((check) => (
                    <span className="failure-chip" key={`${check.name}-${check.status}`}>
                      {(check.name || "check").toLowerCase()} · {(check.status || "unknown").toLowerCase()}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="panel run-summary-panel">
              <div className="panel-head">
                <strong>Fallback state</strong>
                <span>{fallback ? "HISTORICAL" : "LOADING"}</span>
              </div>
              <div className="attempt-summary">
                <div>
                  <span className="attempt-label">Review summary</span>
                  <strong>
                    {fallback?.summary?.verification?.state
                      ? `Verification ${fallback.summary.verification.state}.`
                      : "No historical review snapshot yet."}
                  </strong>
                </div>
                <div>
                  <span className="attempt-label">Changed files</span>
                  <strong>
                    {fallbackFiles.length > 0
                      ? fallbackFiles.map((file) => file.path).filter(Boolean).join(", ")
                      : "Waiting for stream or snapshot details."}
                  </strong>
                </div>
              </div>
            </div>
          </div>

          <div className="panel" style={{ marginTop: 24 }}>
            <div className="panel-body pad event-empty">
              Waiting for the live ledger stream from <code>/api/cbc/runs/{runId}/stream</code>.
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="meta-grid">
            <Meta label="Task" value={ledger.task_id} />
            <Meta label="Mode" value={ledger.mode} />
            <Meta label="Controller" value={ledger.controller_mode} />
            <Meta label="Attempts" value={String(attempts.length)} />
            <Meta label="Unsafe claims" value={String(ledger.unsafe_claims ?? 0)} />
            <Meta label="Model calls" value={String(ledger.model_calls_used ?? 0)} />
            <Meta label="Selected candidate" value={ledger.selected_candidate_id ?? "—"} />
            <Meta label="Started" value={formatTs(ledger.started_at)} />
            <Meta label="Ended" value={formatTs(ledger.ended_at)} />
            <Meta label="Tokens" value={typeof ledger.total_tokens === "number" ? formatCompact(ledger.total_tokens) : "—"} />
            <Meta
              label="Est. cost"
              value={typeof ledger.estimated_cost_usd === "number" ? `$${ledger.estimated_cost_usd.toFixed(4)}` : "—"}
            />
          </div>

          <div className="run-layout">
            <div className="panel run-summary-panel">
              <div className="panel-head">
                <strong>Final summary</strong>
                <span>RUN-LEVEL VIEW</span>
              </div>
              <div className="run-summary-copy">{ledger.final_summary || "No final summary recorded yet."}</div>
              {latest?.verification?.failure_mode_ledger && latest.verification.failure_mode_ledger.length > 0 && (
                <div className="failure-chip-row">
                  {latest.verification.failure_mode_ledger.map((item) => (
                    <span className="failure-chip" key={item}>
                      {item}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="panel run-summary-panel">
              <div className="panel-head">
                <strong>Latest attempt</strong>
                <span>ATTEMPT {latest?.attempt ?? "—"}</span>
              </div>
              <div className="attempt-summary">
                <div>
                  <span className="attempt-label">Claim</span>
                  <strong>{latest?.model_response?.summary || "No model summary recorded."}</strong>
                </div>
                <div>
                  <span className="attempt-label">Verifier</span>
                  <strong>{latest?.verification?.summary || "Awaiting verification details."}</strong>
                </div>
              </div>
              {latest?.adapter_failure_reason && (
                <div className="attempt-warning">{latest.adapter_failure_reason}</div>
              )}
            </div>
          </div>

          <div className="panel" style={{ marginTop: 24 }}>
            <div className="panel-head">
              <strong>Attempt trace</strong>
              <span>{attempts.length} ATTEMPT{attempts.length === 1 ? "" : "S"}</span>
            </div>
            {attempts.length === 0 ? (
              <div className="panel-body pad event-empty">No attempts recorded yet.</div>
            ) : (
              <div className="attempt-list">
                {attempts.map((attempt) => {
                  const verification = attempt.verification;
                  const changed = verification?.changed_files ?? [];
                  const checks = verification?.checks ?? [];
                  return (
                    <div className="attempt-card" key={attempt.attempt}>
                      <div className="attempt-card-head">
                        <div>
                          <div className="attempt-card-kicker">
                            Attempt {attempt.attempt}
                            {attempt.candidate_role ? ` · ${attempt.candidate_role}` : ""}
                            {attempt.candidate_id ? ` · ${attempt.candidate_id}` : ""}
                          </div>
                          <div className="attempt-card-title">
                            {verification?.summary || attempt.model_response?.summary || "No summary"}
                          </div>
                        </div>
                        <span className={`verdict ${(verification?.verdict || "UNKNOWN").toUpperCase()}`}>
                          {(verification?.verdict || "UNKNOWN").toUpperCase()}
                        </span>
                      </div>

                      {checks.length > 0 && (
                        <div className="attempt-check-grid">
                          {checks.map((check, index) => (
                            <div className="attempt-check" key={`${attempt.attempt}-${check.name || index}`}>
                              <span>{check.name || "check"}</span>
                              <span>{(check.status || "unknown").toUpperCase()}</span>
                              <span>{typeof check.duration_seconds === "number" ? `${check.duration_seconds.toFixed(2)}s` : "—"}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {changed.length > 0 && (
                        <div className="attempt-files">
                          {changed.map((file) => (
                            <span className="run-card-file" key={file}>
                              {file}
                            </span>
                          ))}
                        </div>
                      )}

                      {verification?.counterexample && (
                        <details className="counterexample">
                          <summary>Counterexample</summary>
                          <pre>{formatCounterexample(verification.counterexample)}</pre>
                        </details>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <details className="panel raw-ledger-panel">
            <summary className="panel-head raw-ledger-summary">
              <strong>Raw ledger JSON</strong>
              <span>FOR DEBUGGING</span>
            </summary>
            <pre className="ledger">{JSON.stringify(ledger, null, 2)}</pre>
          </details>
        </>
      )}
    </>
  );
}

function Meta({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="meta-cell">
      <div className="meta-label">{label}</div>
      <div className="meta-value">{value || "—"}</div>
    </div>
  );
}

function formatTs(iso?: string): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toISOString().replace("T", " ").replace(/\..*$/, "") + "Z";
  } catch {
    return iso;
  }
}

function formatCompact(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return String(n);
}

function formatCounterexample(value: string | Record<string, unknown>) {
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}
