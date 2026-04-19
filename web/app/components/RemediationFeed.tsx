"use client";

import { useEffect, useState } from "react";
import { getSupabase, type CbcRemediationRow } from "@/lib/supabase";
import { RemediationBadge } from "./RemediationBadge";

export function RemediationFeed() {
  const [rows, setRows] = useState<CbcRemediationRow[]>([]);
  const [configured, setConfigured] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const sb = getSupabase();
    if (!sb) {
      setConfigured(false);
      setLoading(false);
      return;
    }
    let cancelled = false;

    (async () => {
      const { data, error } = await sb
        .from("cbc_remediations")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(10);
      if (!cancelled) {
        if (!error && data) setRows(data as CbcRemediationRow[]);
        setLoading(false);
      }
    })();

    const handleChange = (payload: {
      eventType?: string;
      new?: CbcRemediationRow;
      old?: CbcRemediationRow;
    }) => {
      if (cancelled) return;
      setRows((prev) => {
        if (payload.eventType === "DELETE") {
          return prev.filter((r) => r.id !== payload.old?.id);
        }
        const incoming = payload.new;
        if (!incoming) return prev;
        const idx = prev.findIndex((r) => r.id === incoming.id);
        if (idx >= 0) {
          const next = prev.slice();
          next[idx] = incoming;
          return next;
        }
        return [incoming, ...prev].slice(0, 10);
      });
    };

    const channel = sb.channel("cbc_remediations_live");
    channel.on(
      "postgres_changes",
      { event: "INSERT", schema: "public", table: "cbc_remediations" },
      (payload: { new: CbcRemediationRow }) =>
        handleChange({ eventType: "INSERT", new: payload.new })
    );
    channel.on(
      "postgres_changes",
      { event: "UPDATE", schema: "public", table: "cbc_remediations" },
      (payload: { new: CbcRemediationRow }) =>
        handleChange({ eventType: "UPDATE", new: payload.new })
    );
    channel.subscribe();

    return () => {
      cancelled = true;
      sb.removeChannel(channel);
    };
  }, []);

  return (
    <div className="panel">
      <div className="panel-head">
        <strong>Remediation feed</strong>
        <span>
          <span className="dot live" style={{ marginRight: 8 }} />
          AUTONOMOUS
        </span>
      </div>
      <div className="rem-feed">
        {!configured ? (
          <div className="event-empty">
            Supabase is not configured.
            <br />
            Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to watch
            autonomous remediations stream in.
          </div>
        ) : loading ? (
          <div className="event-empty">Loading remediations…</div>
        ) : rows.length === 0 ? (
          <div className="event-empty">
            No remediations yet.
            <br />
            When a run falsifies, an agent will pick it up — results appear here.
          </div>
        ) : (
          <table className="rem-feed-table">
            <thead>
              <tr>
                <th>Task</th>
                <th>Status</th>
                <th>Attempts</th>
                <th>Cost</th>
                <th>Created</th>
                <th>PR</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="rem-feed-task">{r.task_id || r.task_path || "—"}</td>
                  <td>
                    <RemediationBadge
                      status={r.status}
                      prUrl={r.pr_url}
                      newRunId={r.new_run_id}
                      attempts={r.attempts_used ?? undefined}
                      costUsd={r.cost_usd ?? undefined}
                      error={r.error}
                    />
                  </td>
                  <td>{r.attempts_used ?? "—"}</td>
                  <td>{typeof r.cost_usd === "number" ? `$${r.cost_usd.toFixed(2)}` : "—"}</td>
                  <td className="rem-feed-ts">{formatRelative(r.created_at)}</td>
                  <td>
                    {r.status === "merged" && r.pr_url ? (
                      <a href={r.pr_url} target="_blank" rel="noreferrer">
                        {prLabel(r.pr_url)}
                      </a>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function prLabel(url: string): string {
  const m = url.match(/\/pull\/(\d+)/);
  return m ? `PR#${m[1]}` : "PR";
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
