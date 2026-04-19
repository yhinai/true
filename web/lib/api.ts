export const API_BASE = "/api/cbc";

export const streamUrl = (runId: string): string =>
  `${API_BASE}/runs/${encodeURIComponent(runId)}/stream`;

export const runsStreamUrl = (): string => `${API_BASE}/runs.stream`;

export type HealthStatus = {
  status: string;
  headless_contract_version?: string;
};

export type RunSummary = {
  run_id: string;
  task_id?: string;
  artifact_path?: string;
  merge_gate_verdict?: string;
  verification_state?: string;
};

export type RunReview = {
  run_id: string;
  task_id?: string;
  artifact_path?: string;
  summary?: {
    verification?: {
      state?: string;
      unsafe_claims?: number;
      checks?: Array<{
        name?: string;
        status?: string;
        command?: string;
      }>;
    };
    diff?: {
      files?: Array<{
        path?: string;
      }>;
    };
    merge_gate?: {
      verdict?: string;
      reason?: string;
    };
  };
};

export async function fetchRuns(): Promise<RunSummary[]> {
  const r = await fetch(`${API_BASE}/runs`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /runs ${r.status}`);
  const body = (await r.json()) as { runs: RunSummary[] };
  return body.runs ?? [];
}

export async function fetchRunReview(runId: string): Promise<RunReview> {
  const r = await fetch(`${API_BASE}/runs/${encodeURIComponent(runId)}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /runs/${runId} ${r.status}`);
  return (await r.json()) as RunReview;
}

export async function fetchHealth(): Promise<HealthStatus> {
  const r = await fetch(`${API_BASE}/health`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /health ${r.status}`);
  return (await r.json()) as HealthStatus;
}
