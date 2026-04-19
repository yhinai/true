"use client";

import { useEffect, useState } from "react";
import { getSupabase } from "@/lib/supabase";

type Stats = {
  total: number;
  verified: number;
  falsified: number;
  timedOut: number;
  unproven: number;
  runs24h: number;
  tokens: number;
  cost: number;
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

        if (row.started_at) {
          const t = new Date(row.started_at).getTime();
          if (!Number.isNaN(t) && now - t < 86400000) s.runs24h++;
        }

        const p = row.payload;
        if (p && typeof p === "object") {
          const tok = (p as { total_tokens?: number }).total_tokens;
          const c = (p as { estimated_cost_usd?: number }).estimated_cost_usd;
          if (typeof tok === "number") tokens += tok;
          if (typeof c === "number") cost += c;
        }
      }
      s.tokens = tokens;
      s.cost = cost;
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
        spark={`${stats.verified}/${stats.falsified}/${stats.timedOut}/${stats.unproven}`}
      />
      <Kpi
        label="Runs · last 24h"
        value={loaded ? String(stats.runs24h) : "—"}
        unit=""
        sub={`${stats.total} total in ledger`}
      />
      <Kpi
        label="Tokens spent"
        value={loaded ? formatCompact(stats.tokens) : "—"}
        unit=""
        sub={`Cumulative across all attempts`}
      />
      <Kpi
        label="Avg cost / run"
        value={avgCost}
        unit={stats.total > 0 ? "USD" : ""}
        sub={`$${stats.cost.toFixed(2)} total`}
      />
    </div>
  );
}

function Kpi({
  label,
  value,
  unit,
  sub,
  spark,
}: {
  label: string;
  value: string;
  unit: string;
  sub: string;
  spark?: string;
}) {
  return (
    <div className="kpi">
      <div className="kpi-label">
        <span>{label}</span>
        {spark && <span className="kpi-spark">{spark}</span>}
      </div>
      <div className="kpi-value">
        <em>{value}</em>
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
      <div className="kpi-sub">{sub}</div>
    </div>
  );
}

function formatCompact(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return String(n);
}
