"use client";

import { useEffect, useState } from "react";
import { getSupabase } from "@/lib/supabase";

type LiveState = {
  configured: boolean;
  loaded: boolean;
  runs: number;
  lastVerdict: string | null;
  lastAt: string | null;
  latencyMs: number | null;
};

const INIT: LiveState = {
  configured: true,
  loaded: false,
  runs: 0,
  lastVerdict: null,
  lastAt: null,
  latencyMs: null,
};

export function Footer() {
  const [live, setLive] = useState<LiveState>(INIT);

  useEffect(() => {
    const sb = getSupabase();
    if (!sb) {
      setLive({ ...INIT, configured: false, loaded: true });
      return;
    }
    let cancelled = false;
    (async () => {
      const t0 =
        typeof performance !== "undefined" ? performance.now() : Date.now();
      const countResp = await sb
        .from("cbc_runs")
        .select("run_id", { count: "exact", head: true });
      const t1 =
        typeof performance !== "undefined" ? performance.now() : Date.now();
      const latencyMs = Math.round(t1 - t0);
      if (cancelled) return;

      const latestResp = await sb
        .from("cbc_runs")
        .select("verdict, started_at")
        .order("started_at", { ascending: false })
        .limit(1);
      if (cancelled) return;

      const runs = countResp.count ?? 0;
      const latest = (latestResp.data?.[0] ?? null) as
        | { verdict: string | null; started_at: string | null }
        | null;

      setLive({
        configured: true,
        loaded: true,
        runs,
        lastVerdict: latest?.verdict ?? null,
        lastAt: latest?.started_at ?? null,
        latencyMs,
      });
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const verdict = (live.lastVerdict || "UNKNOWN").toUpperCase();

  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-block">
          <strong>System</strong>
          <ul>
            <li>CBC command center</li>
            <li>Python 3.11 · FastAPI</li>
            <li>Next.js 16 · React 19</li>
            <li>Supabase mirror · optional</li>
          </ul>
        </div>
        <div className="footer-block">
          <strong>Live state</strong>
          <ul>
            <li>
              {live.configured ? (
                live.loaded ? (
                  <>
                    <span className="ok">● Ledger</span>{" "}
                    <span className="footer-mono">{live.runs} runs</span>
                  </>
                ) : (
                  <>
                    <span className="warn">● Probing ledger…</span>
                  </>
                )
              ) : (
                <>
                  <span className="warn">● Supabase unset</span>
                </>
              )}
            </li>
            <li>
              {live.lastAt ? (
                <>
                  <span className={`footer-verdict ${verdict}`}>● {verdict}</span>{" "}
                  <span className="footer-mono">{formatRelative(live.lastAt)}</span>
                </>
              ) : live.configured && live.loaded ? (
                <span className="warn">● No runs yet</span>
              ) : (
                <span className="muted">● awaiting latest</span>
              )}
            </li>
            <li>
              {live.latencyMs !== null ? (
                <>
                  <span className="ok">● Supabase probe</span>{" "}
                  <span className="footer-mono">{live.latencyMs}ms</span>
                </>
              ) : live.configured ? (
                <span className="muted">● latency —</span>
              ) : (
                <span className="muted">● probe offline</span>
              )}
            </li>
            <li>
              <span className="ok">● Same-origin API proxy on Vercel</span>
            </li>
          </ul>
        </div>
        <div className="footer-block">
          <strong>Verdict handles</strong>
          <ul>
            <li>VERIFIED · oracle + suite pass</li>
            <li>FALSIFIED · counterexample found</li>
            <li>TIMED_OUT · wall budget exceeded</li>
            <li>UNPROVEN · inconclusive</li>
          </ul>
        </div>
        <div className="footer-block">
          <strong>Deployment</strong>
          <ul>
            <li>Vercel web edge</li>
            <li>CBC API behind explicit env</li>
            <li>Security headers via vercel.json</li>
          </ul>
        </div>
      </div>
    </footer>
  );
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
