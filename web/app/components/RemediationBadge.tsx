"use client";

type Props = {
  status: string;
  prUrl?: string | null;
  newRunId?: string | null;
  attempts?: number;
  costUsd?: number;
  error?: string | null;
};

export function RemediationBadge({
  status,
  prUrl,
  newRunId: _newRunId,
  attempts,
  costUsd,
  error,
}: Props) {
  const s = (status || "unknown").toLowerCase();
  const label = labelFor(s);
  const tone = toneFor(s);

  const prNumber = extractPrNumber(prUrl ?? null);

  return (
    <span className={`rem-badge rem-${tone}`} title={tooltipFor(s, error)}>
      <span className="rem-badge-dot" />
      <span className="rem-badge-label">{label}</span>

      {s === "merged" && prUrl && prNumber && (
        <a
          className="rem-badge-pr"
          href={prUrl}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
        >
          → PR#{prNumber}
        </a>
      )}

      {s === "bailed_budget" && typeof costUsd === "number" && (
        <span className="rem-badge-note">${costUsd.toFixed(2)}</span>
      )}

      {s === "bailed_loop" && typeof attempts === "number" && (
        <span className="rem-badge-note">repeat {attempts}×</span>
      )}

      {s === "error" && (
        <span
          className="rem-badge-note rem-badge-error"
          title={error ? truncate(error, 200) : "error"}
        >
          (!)
        </span>
      )}
    </span>
  );
}

function labelFor(s: string): string {
  switch (s) {
    case "queued":
      return "queued";
    case "running":
      return "running";
    case "merged":
      return "merged";
    case "bailed_budget":
      return "bailed · budget";
    case "bailed_loop":
      return "bailed · loop";
    case "error":
      return "error";
    default:
      return s || "unknown";
  }
}

function toneFor(s: string): string {
  switch (s) {
    case "merged":
      return "ok";
    case "running":
    case "queued":
      return "amber";
    case "bailed_budget":
    case "bailed_loop":
    case "error":
      return "bad";
    default:
      return "dim";
  }
}

function tooltipFor(s: string, error?: string | null): string {
  if (s === "error" && error) return truncate(error, 240);
  return `remediation: ${s}`;
}

function extractPrNumber(url: string | null): string | null {
  if (!url) return null;
  const m = url.match(/\/pull\/(\d+)/);
  return m ? m[1] : null;
}

function truncate(s: string, n: number): string {
  if (!s) return "";
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}
