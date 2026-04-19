export const API_BASE: string =
  process.env.NEXT_PUBLIC_CBC_API_URL || "http://localhost:8000";

export const streamUrl = (runId: string): string =>
  `${API_BASE}/runs/${encodeURIComponent(runId)}/stream`;

export const runsStreamUrl = (): string => `${API_BASE}/runs.stream`;

export type RunSummary = {
  run_id: string;
  task_id?: string;
  artifact_path?: string;
  merge_gate_verdict?: string;
  verification_state?: string;
};

export async function fetchRuns(): Promise<RunSummary[]> {
  const r = await fetch(`${API_BASE}/runs`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /runs ${r.status}`);
  const body = (await r.json()) as { runs: RunSummary[] };
  return body.runs ?? [];
}
