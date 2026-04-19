"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";

type ApiState =
  | { state: "loading" }
  | { state: "ready"; contract?: string }
  | { state: "error"; message: string };

export function RuntimeStatus() {
  const [api, setApi] = useState<ApiState>({ state: "loading" });
  const supabaseConfigured = Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((payload) => {
        if (cancelled) return;
        setApi({ state: "ready", contract: payload.headless_contract_version });
      })
      .catch((error) => {
        if (cancelled) return;
        setApi({ state: "error", message: error instanceof Error ? error.message : String(error) });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="runtime-strip">
      <div className="runtime-card">
        <div className="runtime-label">API proxy</div>
        <div className="runtime-value">
          {api.state === "ready" ? "reachable" : api.state === "loading" ? "probing" : "misconfigured"}
        </div>
        <div className="runtime-sub">
          {api.state === "ready"
            ? `Same-origin route is healthy${api.contract ? ` · contract ${api.contract}` : ""}.`
            : api.state === "loading"
            ? "Checking /api/cbc/health now."
            : `Set CBC_API_URL in Vercel or your local shell. ${api.message}`}
        </div>
      </div>

      <div className="runtime-card">
        <div className="runtime-label">Supabase mirror</div>
        <div className="runtime-value">{supabaseConfigured ? "configured" : "optional"}</div>
        <div className="runtime-sub">
          {supabaseConfigured
            ? "Fleet-wide KPIs and event history can hydrate from mirrored run data."
            : "The app still works without Supabase; aggregate KPIs and realtime event history simply stay offline."}
        </div>
      </div>

      <div className="runtime-card">
        <div className="runtime-label">Deploy mode</div>
        <div className="runtime-value">vercel-safe</div>
        <div className="runtime-sub">
          Browser traffic stays same-origin and the server-side proxy owns the backend URL.
        </div>
      </div>
    </div>
  );
}
