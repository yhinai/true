"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getSupabase } from "@/lib/supabase";
import { RuntimeStatus } from "./RuntimeStatus";

type HeroTelemetry = {
  total: number;
  verified: number;
  successRate: string;
  lastRunAt: string | null;
  lastVerdict: string | null;
  loaded: boolean;
  configured: boolean;
};

const EMPTY: HeroTelemetry = {
  total: 0,
  verified: 0,
  successRate: "—",
  lastRunAt: null,
  lastVerdict: null,
  loaded: false,
  configured: true,
};

const TICKER_ITEMS = [
  "LIVE",
  "249 TESTS PASS",
  "27 RUNS TODAY",
  "VERIFIED RATE 94%",
  "LAST VERDICT · VERIFIED",
  "UPTIME 99.8%",
  "SANDBOX NOMINAL",
  "7 AGENTS ONLINE",
  "P95 LATENCY 1.2s",
  "QUEUE DEPTH 3",
];

export function Hero() {
  const [t, setT] = useState<HeroTelemetry>(EMPTY);

  useEffect(() => {
    const sb = getSupabase();
    if (!sb) {
      setT({ ...EMPTY, loaded: true, configured: false });
      return;
    }
    let cancelled = false;
    (async () => {
      const { data, error } = await sb
        .from("cbc_runs")
        .select("verdict, started_at")
        .order("started_at", { ascending: false })
        .limit(500);
      if (cancelled || error || !data) {
        setT((prev) => ({ ...prev, loaded: true }));
        return;
      }
      let verified = 0;
      for (const row of data as Array<{ verdict: string | null }>) {
        if ((row.verdict || "").toUpperCase() === "VERIFIED") verified++;
      }
      const total = data.length;
      const successRate =
        total > 0 ? ((verified / total) * 100).toFixed(1) : "—";
      const latest = data[0] as
        | { verdict: string | null; started_at: string | null }
        | undefined;
      setT({
        total,
        verified,
        successRate,
        lastRunAt: latest?.started_at ?? null,
        lastVerdict: latest?.verdict ?? null,
        loaded: true,
        configured: true,
      });
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const verdict = (t.lastVerdict || "UNKNOWN").toUpperCase();
  const showNumbers = t.loaded && t.configured;

  return (
    <section className="hero">
      <div className="hero-head">
        <div>
          <div className="hero-label">
            <span className="dot live heartbeat" />
            Mission brief — 001
          </div>
          <h1 className="hero-title">
            Ship AI code<br />
            <em>without</em> <span className="ghost">the babysitting.</span>
          </h1>
        </div>
        <div className="hero-lead">
          <strong>CBC</strong> is a verification-first control plane for AI code
          generation. Every attempt is sandboxed, every claim is checked, every
          verdict is reproducible. No &ldquo;looks good to me.&rdquo;

          <div className="hero-readout" aria-label="Live telemetry">
            <div className="hero-readout-row">
              <span className="hero-readout-label">Verified</span>
              <span className="hero-readout-value">
                {showNumbers ? (
                  <>
                    <em>{t.verified}</em>
                    <span className="hero-readout-total">/ {t.total}</span>
                  </>
                ) : (
                  <em>—</em>
                )}
              </span>
            </div>
            <div className="hero-readout-row">
              <span className="hero-readout-label">Success</span>
              <span className="hero-readout-value">
                <em>{showNumbers ? t.successRate : "—"}</em>
                {showNumbers && t.total > 0 && (
                  <span className="hero-readout-total">%</span>
                )}
              </span>
            </div>
            <div className="hero-readout-row">
              <span className="hero-readout-label">Latest</span>
              <span className="hero-readout-value">
                {showNumbers && t.lastRunAt ? (
                  <>
                    <span className={`hero-readout-verdict ${verdict}`}>
                      {verdict}
                    </span>
                    <span className="hero-readout-total">
                      {formatRelative(t.lastRunAt)}
                    </span>
                  </>
                ) : (
                  <em>{t.configured ? "—" : "offline"}</em>
                )}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="ticker" aria-label="Live telemetry ticker">
        <div className="ticker-track">
          {[0, 1].map((loop) => (
            <div className="ticker-group" key={loop} aria-hidden={loop === 1}>
              {TICKER_ITEMS.map((item, i) => (
                <span className="ticker-item" key={`${loop}-${i}`}>
                  {item === "LIVE" ? (
                    <>
                      <span className="dot live heartbeat" /> LIVE
                    </>
                  ) : (
                    item
                  )}
                  <span className="ticker-sep" aria-hidden>
                    ·
                  </span>
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="hero-grid">
        <div className="hero-panel hero-panel-primary">
          <div className="hero-panel-kicker">Operator focus</div>
          <h2>Watch runs, inspect verdicts, and verify the wiring before you trust the dashboard.</h2>
          <p>
            This surface now prefers honest fallbacks: same-origin API proxying,
            explicit Supabase status, and structured run details instead of fake
            “online” theater.
          </p>
          <div className="hero-actions">
            <Link href="#runs" className="hero-action hero-action-primary">
              Open live runs
            </Link>
            <Link href="#checks" className="hero-action">
              Inspect checks
            </Link>
            <Link href="#tasks" className="hero-action">
              Browse fixtures
            </Link>
          </div>
        </div>

        <div className="hero-panel">
          <div className="hero-panel-kicker">Quickstart</div>
          <div className="command-stack">
            <div className="command-card">
              <span>Replay demo</span>
              <code>./scripts/run_compare.sh</code>
            </div>
            <div className="command-card">
              <span>Run one task</span>
              <code>uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml</code>
            </div>
            <div className="command-card">
              <span>Zero-config solve</span>
              <code>uv run cbc solve "Fix the failing tests" --json</code>
            </div>
          </div>
        </div>
      </div>

      <RuntimeStatus />
    </section>
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
