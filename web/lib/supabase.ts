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
