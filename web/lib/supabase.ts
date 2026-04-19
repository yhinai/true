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
