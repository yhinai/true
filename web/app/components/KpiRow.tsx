"use client";

import { useEffect, useState } from "react";
import { getSupabase } from "@/lib/supabase";

type RunPoint = {
  verified: number; // 0 or 1
  ts: number;
  tokens: number;
  cost: number;
};

type Stats = {
  total: number;
  verified: number;
  falsified: number;
  timedOut: number;
  unproven: number;
  runs24h: number;
  tokens: number;
  cost: number;
  // Oldest -> newest, up to 20 points
  successSeries: number[]; // 0 | 1
  runsPerHourSeries: number[]; // bucketed count
  tokensSeries: number[]; // per-run tokens
  costSeries: number[]; // per-run cost
};

const EMPTY: Stats = {
  total: 0,
  verified: 0,
  falsified: 0,
  timedOut: 0,
  unproven: 0,
  runs24h: 0,
  tokens: 0,
  cost: 0,
  successSeries: [],
  runsPerHourSeries: [],
  tokensSeries: [],
  costSeries: [],
};

export function KpiRow() {
  const [stats, setStats] = useState<Stats>(EMPTY);
  const [loaded, setLoaded] = useState(false);
  const [configured, setConfigured] = useState(true);

  useEffect(() => {
    const sb = getSupabase();
    if (!sb) {
      setConfigured(false);
      setLoaded(true);
      return;
    }
    let cancelled = false;

    (async () => {
      const { data, error } = await sb
        .from("cbc_runs")
        .select("run_id, verdict, started_at, payload")
        .order("started_at", { ascending: false })
        .limit(500);
      if (cancelled || error || !data) {
        setLoaded(true);
        return;
      }

      const now = Date.now();
      let tokens = 0;
      let cost = 0;
      const s: Stats = { ...EMPTY, total: data.length };
      const points: RunPoint[] = [];

      for (const row of data as Array<{
        verdict: string | null;
        started_at: string | null;
        payload: Record<string, unknown> | null;
      }>) {
        const v = (row.verdict || "").toUpperCase();
        if (v === "VERIFIED") s.verified++;
        else if (v === "FALSIFIED") s.falsified++;
        else if (v === "TIMED_OUT") s.timedOut++;
        else if (v === "UNPROVEN") s.unproven++;

        let ts = 0;
        if (row.started_at) {
          const t = new Date(row.started_at).getTime();
          if (!Number.isNaN(t)) {
            ts = t;
            if (now - t < 86400000) s.runs24h++;
          }
        }

        let runTok = 0;
        let runCost = 0;
        const p = row.payload;
        if (p && typeof p === "object") {
          const tok = (p as { total_tokens?: number }).total_tokens;
          const c = (p as { estimated_cost_usd?: number }).estimated_cost_usd;
          if (typeof tok === "number") {
            tokens += tok;
            runTok = tok;
          }
          if (typeof c === "number") {
            cost += c;
            runCost = c;
          }
        }

        if (ts > 0) {
          points.push({
            verified: v === "VERIFIED" ? 1 : 0,
            ts,
            tokens: runTok,
            cost: runCost,
          });
        }
      }
      s.tokens = tokens;
      s.cost = cost;

      // points is newest-first → reverse to oldest-first, take last 20
      const oldestFirst = points.reverse();
      const recent = oldestFirst.slice(-20);
      s.successSeries = recent.map((p) => p.verified);
      s.tokensSeries = recent.map((p) => p.tokens);
      s.costSeries = recent.map((p) => p.cost);

      // bucket last 20 hours for runs-per-hour
      if (recent.length > 0) {
        const buckets = new Array(20).fill(0);
        const nowH = Math.floor(now / 3_600_000);
        for (const pt of points) {
          const hr = Math.floor(pt.ts / 3_600_000);
          const idx = 19 - (nowH - hr);
          if (idx >= 0 && idx < 20) buckets[idx]++;
        }
        s.runsPerHourSeries = buckets;
      }

      setStats(s);
      setLoaded(true);
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const successRate =
    stats.total > 0 ? ((stats.verified / stats.total) * 100).toFixed(1) : "—";
  const avgCost = stats.total > 0 ? (stats.cost / stats.total).toFixed(4) : "—";

  if (!configured) {
    return (
      <div className="kpi-grid">
        <Kpi
          label="Supabase mirror"
          value="optional"
          unit=""
          sub="Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to light up aggregate telemetry."
        />
        <Kpi
          label="Run stream"
          value="ready"
          unit=""
          sub="Live run tails still work through the API proxy and SSE."
        />
        <Kpi
          label="Dashboard mode"
          value="honest"
          unit=""
          sub="No fake totals when telemetry storage is not configured."
        />
        <Kpi
          label="Next step"
          value="mirror"
          unit=""
          sub="Mirror ledgers to Supabase if you want fleet-wide KPIs and event history."
        />
      </div>
    );
  }

  return (
    <div className="kpi-grid">
      <Kpi
        label="Verified rate"
        value={successRate}
        unit={stats.total > 0 ? "%" : ""}
        sub={`${stats.verified} of ${stats.total} runs`}
        series={stats.successSeries}
      />
      <Kpi
        label="Runs · last 24h"
        value={loaded ? String(stats.runs24h) : "—"}
        unit=""
        sub={`${stats.total} total in ledger`}
        series={stats.runsPerHourSeries}
      />
      <Kpi
        label="Tokens spent"
        value={loaded ? formatCompact(stats.tokens) : "—"}
        unit=""
        sub={`Cumulative across all attempts`}
        series={stats.tokensSeries}
      />
      <Kpi
        label="Avg cost / run"
        value={avgCost}
        unit={stats.total > 0 ? "USD" : ""}
        sub={`$${stats.cost.toFixed(2)} total`}
        series={stats.costSeries}
      />
    </div>
  );
}

function Kpi({
  label,
  value,
  unit,
  sub,
  series,
}: {
  label: string;
  value: string;
  unit: string;
  sub: string;
  series?: number[];
}) {
  return (
    <div className="kpi">
      <div className="kpi-label">
        <span>{label}</span>
        {series && series.length > 1 && <Sparkline data={series} />}
      </div>
      <div className="kpi-value">
        <em>{value}</em>
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
      <div className="kpi-sub">{sub}</div>
    </div>
  );
}

function Sparkline({ data }: { data: number[] }) {
  const w = 80;
  const h = 22;
  const pad = 1;
  // normalize
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const stepX = (w - pad * 2) / Math.max(1, data.length - 1);
  const points = data
    .map((v, i) => {
      const x = pad + i * stepX;
      const y = pad + (h - pad * 2) * (1 - (v - min) / range);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  // baseline (mean)
  const mean = data.reduce((a, b) => a + b, 0) / data.length;
  const meanY = pad + (h - pad * 2) * (1 - (mean - min) / range);

  return (
    <svg
      className="kpi-sparkline"
      width={w}
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      aria-hidden="true"
    >
      <line
        x1={pad}
        y1={meanY.toFixed(1)}
        x2={w - pad}
        y2={meanY.toFixed(1)}
        stroke="var(--dim)"
        strokeWidth="1"
        strokeDasharray="2 2"
      />
      <polyline
        fill="none"
        stroke="var(--amber)"
        strokeWidth="1.25"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

function formatCompact(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return String(n);
}
