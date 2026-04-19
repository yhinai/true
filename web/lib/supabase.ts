"use client";

import { createClient, SupabaseClient } from "@supabase/supabase-js";

let cached: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient | null {
  if (cached) return cached;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  cached = createClient(url, key, {
    auth: { persistSession: false },
  });
  return cached;
}

export type CbcRunRow = {
  run_id: string;
  task_id: string | null;
  title: string | null;
  mode: string | null;
  verdict: string | null;
  adapter: string | null;
  started_at: string | null;
  ended_at: string | null;
  payload: Record<string, unknown>;
  inserted_at: string;
};

export async function fetchLedgerFromSupabase(
  runId: string
): Promise<Record<string, unknown> | null> {
  const sb = getSupabase();
  if (!sb) return null;
  const { data, error } = await sb
    .from("cbc_runs")
    .select("run_id, task_id, title, verdict, started_at, ended_at, payload")
    .eq("run_id", runId)
    .maybeSingle();
  if (error || !data) return null;
  const payload = (data.payload as Record<string, unknown> | null) || {};
  return {
    ...payload,
    run_id: payload.run_id ?? data.run_id,
    task_id: payload.task_id ?? data.task_id ?? undefined,
    title: payload.title ?? data.title ?? undefined,
    verdict: payload.verdict ?? data.verdict ?? undefined,
    started_at: payload.started_at ?? data.started_at ?? undefined,
    ended_at: payload.ended_at ?? data.ended_at ?? undefined,
  };
}

export type CbcRemediationRow = {
  id: number;
  run_id: string;
  task_id: string | null;
  task_path: string | null;
  status: string;
  attempts_used: number | null;
  cost_usd: number | null;
  pr_url: string | null;
  new_run_id: string | null;
  error: string | null;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
};
