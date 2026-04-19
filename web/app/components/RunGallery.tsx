"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchRuns, runsStreamUrl, type RunSummary } from "@/lib/api";
import { getSupabase, type CbcRemediationRow } from "@/lib/supabase";
import { useSSE } from "@/lib/useSSE";
import { RemediationBadge } from "./RemediationBadge";

type RunRow = {
  run_id: string;
  task_id: string | null;
  title: string | null;
  mode: string | null;
  verdict: string | null;
  adapter: string | null;
  started_at: string | null;
  ended_at: string | null;
  payload: Record<string, unknown> | null;
};

type RichRun = {
  run_id: string;
  task_id: string;
  title: string;
  mode: string;
  verdict: string;
  adapter: string;
  started_at: string | null;
  ended_at: string | null;
  elapsed: number | null;
  attempts: number;
  checks: Array<{ name: string; status: string }>;
  changed: string[];
  tokens: number | null;
  cost: number | null;
  claimedSuccess: boolean | null;
};

export function RunGallery() {
  const [runs, setRuns] = useState<RichRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<"sse" | "rest" | "supabase" | "empty">("empty");
  const [remediations, setRemediations] = useState<Record<string, CbcRemediationRow>>({});

  const sse = useSSE<RunSummary[]>(runsStreamUrl(), ["runs"]);

  useEffect(() => {
    if (!sse.data) return;
    setRuns(sse.data.map(enrichSummary));
    setSource(sse.data.length ? "sse" : "empty");
    setLoading(false);
  }, [sse.data]);

  useEffect(() => {
    if (sse.connected || sse.data) return;
    let cancelled = false;
    fetchRuns()
      .then((data) => {
        if (cancelled) return;
        setRuns(data.map(enrichSummary));
        setSource(data.length ? "rest" : "empty");
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [sse.connected, sse.data]);

  useEffect(() => {
    if (runs.length > 0) return;
    const sb = getSupabase();
    if (!sb) {
      setLoading(false);
      return;
    }
    let cancelled = false;

    (async () => {
      const { data, error } = await sb
        .from("cbc_runs")
        .select("run_id, task_id, title, mode, verdict, adapter, started_at, ended_at, payload")
        .order("started_at", { ascending: false })
        .limit(50);
      if (cancelled || error || !data) {
        setLoading(false);
        return;
      }
      const enriched = (data as RunRow[]).map(enrich);
      setRuns(enriched);
      setSource(enriched.length ? "supabase" : "empty");
      setLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (runs.length === 0) return;
    const sb = getSupabase();
    if (!sb) return;
    let cancelled = false;
    const ids = runs.map((r) => r.run_id);

    (async () => {
      const { data, error } = await sb
        .from("cbc_remediations")
        .select("*")
        .in("run_id", ids);
      if (cancelled || error || !data) return;
      const map: Record<string, CbcRemediationRow> = {};
      for (const row of data as CbcRemediationRow[]) {
        const existing = map[row.run_id];
        if (!existing) {
          map[row.run_id] = row;
          continue;
        }
        const a = existing.created_at ? Date.parse(existing.created_at) : 0;
        const b = row.created_at ? Date.parse(row.created_at) : 0;
        if (b >= a) map[row.run_id] = row;
      }
      setRemediations(map);
    })();

    return () => {
      cancelled = true;
    };
  }, [runs]);

  if (loading) {
    return (
      <div className="panel">
        <div className="panel-body pad event-empty">Loading ledger…</div>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="panel">
        <div className="panel-body pad event-empty">
          No runs in the ledger yet.
          <br />
          <span style={{ color: "var(--dim)", fontSize: 11 }}>
            Kick one off with <code style={{ color: "var(--amber)" }}>uv run cbc run …</code>.
            This gallery reads from the CBC API first and only relies on Supabase for richer enrichment.
          </span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="gallery-source">
        <span className={`dot ${source === "sse" ? "live" : "amber"}`} />
        {source === "sse"
          ? "Live from runs.stream"
          : source === "rest"
          ? "API snapshot"
          : source === "supabase"
          ? "Supabase-enriched snapshot"
          : "Awaiting signal"}
      </div>
      <div className="run-gallery">
        {runs.map((r) => (
          <RunCard key={r.run_id} run={r} remediation={remediations[r.run_id]} />
        ))}
      </div>
    </>
  );
}

function RunCard({
  run,
  remediation,
}: {
  run: RichRun;
  remediation?: CbcRemediationRow;
}) {
  const verdict = run.verdict.toUpperCase();
  const visibleChecks = run.checks.slice(0, 3);
  const extraChecks = run.checks.slice(3);
  const extraTitle = extraChecks
    .map((c) => `${c.name} · ${c.status}`)
    .join("\n");
  return (
    <Link
      href={`/runs/${run.run_id}`}
      className={`run-card run-card-verdict-${verdict}`}
    >
      <div className="run-card-top">
        <div className="run-card-tag">
          <span className="run-card-idx">{run.run_id.slice(0, 12)}</span>
          <span className="run-card-dot">/</span>
          <span className="run-card-task">{run.task_id}</span>
        </div>
        <div className="run-card-verdicts">
          <span className={`verdict ${verdict}`}>{verdict}</span>
          {remediation && (
            <RemediationBadge
              status={remediation.status}
              prUrl={remediation.pr_url}
              newRunId={remediation.new_run_id}
              attempts={remediation.attempts_used ?? undefined}
              costUsd={remediation.cost_usd ?? undefined}
              error={remediation.error}
            />
          )}
        </div>
      </div>

      <div className="run-card-title">{run.title || run.task_id}</div>

      <div className="run-card-meta">
        <span>{run.mode || "—"}</span>
        {run.elapsed !== null && (
          <>
            <span className="sep" />
            <span>{run.elapsed.toFixed(2)}s</span>
          </>
        )}
        {run.attempts > 0 && (
          <>
            <span className="sep" />
            <span>
              {run.attempts} attempt{run.attempts === 1 ? "" : "s"}
            </span>
          </>
        )}
        {run.tokens !== null && (
          <>
            <span className="sep" />
            <span>{formatCompact(run.tokens)} tok</span>
          </>
        )}
      </div>

      {remediation?.status === "merged" && remediation.new_run_id && (
        <div className="run-card-remediated">
          <Link
            href={`/runs/${remediation.new_run_id}`}
            className="run-card-remediated-link"
            onClick={(e) => e.stopPropagation()}
          >
            see remediated run →
          </Link>
        </div>
      )}

      {run.checks.length > 0 && (
        <div className="run-card-checks">
          {visibleChecks.map((c, i) => (
            <span
              key={i}
              className={`check-pill ${c.status.toUpperCase()}`}
              title={c.name}
            >
              <span className="check-pill-dot" />
              {c.name}
            </span>
          ))}
          {extraChecks.length > 0 && (
            <span
              className="check-pill check-pill-more"
              title={extraTitle}
              onClick={(e) => e.preventDefault()}
            >
              +{extraChecks.length} more
            </span>
          )}
        </div>
      )}

      {run.changed.length > 0 && (
        <div className="run-card-changed">
          <span className="run-card-changed-label">Δ</span>
          {run.changed.slice(0, 3).map((f, i) => (
            <span key={i} className="run-card-file">
              {f}
            </span>
          ))}
          {run.changed.length > 3 && (
            <span className="run-card-file more">+{run.changed.length - 3}</span>
          )}
        </div>
      )}

      <div className="run-card-ts">
        {formatRelative(run.started_at)}
        <span className="run-card-arrow">→</span>
      </div>
    </Link>
  );
}

function enrich(row: RunRow): RichRun {
  const p = row.payload ?? {};
  const attempts = Array.isArray((p as { attempts?: unknown[] }).attempts)
    ? ((p as { attempts: Record<string, unknown>[] }).attempts as Record<string, unknown>[])
    : [];
  const last = attempts[attempts.length - 1];
  const verification = (last?.verification as Record<string, unknown> | undefined) ?? {};
  const rawChecks = Array.isArray(verification.checks)
    ? (verification.checks as Array<Record<string, unknown>>)
    : [];
  const checks = rawChecks.map((c) => ({
    name: String(c.name ?? "?"),
    status: normalizeStatus(String(c.status ?? "")),
  }));
  const changed = Array.isArray(verification.changed_files)
    ? (verification.changed_files as string[])
    : [];
  const mr = (last?.model_response as Record<string, unknown> | undefined) ?? {};
  const claimed =
    typeof mr.claimed_success === "boolean" ? (mr.claimed_success as boolean) : null;
  const tokens =
    typeof (p as { total_tokens?: unknown }).total_tokens === "number"
      ? ((p as { total_tokens: number }).total_tokens as number)
      : null;
  const cost =
    typeof (p as { estimated_cost_usd?: unknown }).estimated_cost_usd === "number"
      ? ((p as { estimated_cost_usd: number }).estimated_cost_usd as number)
      : null;

  return {
    run_id: row.run_id,
    task_id: row.task_id ?? "—",
    title:
      row.title ??
      (typeof (p as { title?: unknown }).title === "string"
        ? ((p as { title: string }).title as string)
        : ""),
    mode: row.mode ?? "—",
    verdict: row.verdict ?? "UNKNOWN",
    adapter: row.adapter ?? "—",
    started_at: row.started_at,
    ended_at: row.ended_at,
    elapsed: elapsed(row.started_at, row.ended_at),
    attempts: attempts.length,
    checks,
    changed,
    tokens,
    cost,
    claimedSuccess: claimed,
  };
}

function enrichSummary(row: RunSummary): RichRun {
  return {
    run_id: row.run_id,
    task_id: row.task_id ?? "—",
    title: row.task_id ?? row.run_id,
    mode: "—",
    verdict: row.verification_state ?? row.merge_gate_verdict ?? "UNKNOWN",
    adapter: "api",
    started_at: null,
    ended_at: null,
    elapsed: null,
    attempts: 0,
    checks: [],
    changed: [],
    tokens: null,
    cost: null,
    claimedSuccess: null,
  };
}

function normalizeStatus(s: string): string {
  const u = s.toUpperCase();
  if (u === "PASSED" || u === "PASS" || u === "OK") return "VERIFIED";
  if (u === "FAILED" || u === "FAIL") return "FALSIFIED";
  if (u === "TIMED_OUT") return "TIMED_OUT";
  if (u === "SKIPPED" || u === "SKIP") return "UNPROVEN";
  return "UNKNOWN";
}

function elapsed(start: string | null, end: string | null): number | null {
  if (!start || !end) return null;
  const s = new Date(start).getTime();
  const e = new Date(end).getTime();
  if (Number.isNaN(s) || Number.isNaN(e)) return null;
  return (e - s) / 1000;
}

function formatRelative(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function formatCompact(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return String(n);
}
