const COMMANDS: Array<{
  id: string;
  name: string;
  desc: string;
  glyph: string;
  flags?: string[];
}> = [
  {
    id: "01",
    name: "cbc run",
    desc: "Execute a task against a sandboxed workspace; iterate until the verification oracle certifies or aborts.",
    glyph: "R",
    flags: ["--mode", "--controller", "--sandbox", "--agent"],
  },
  {
    id: "02",
    name: "cbc solve",
    desc: "Free-form prompt → synthetic task spec → bounded solve loop with auto-generated oracles.",
    glyph: "S",
    flags: ["--prompt", "--max-attempts"],
  },
  {
    id: "03",
    name: "cbc compare",
    desc: "A/B benchmark baseline vs. treatment across a curated oracle subset; emits delta report.",
    glyph: "C",
    flags: ["--baseline", "--treatment", "--seed"],
  },
  {
    id: "04",
    name: "cbc controller-compare",
    desc: "Race sequential vs. gearbox orchestration on the same task set. Latency + verdict stats.",
    glyph: "V",
  },
  {
    id: "05",
    name: "cbc poc",
    desc: "Live Codex sampling: seeded repeats, pairwise stats, confidence intervals.",
    glyph: "P",
    flags: ["--seed", "--sample-size"],
  },
  {
    id: "06",
    name: "cbc review",
    desc: "Generate a structured code-review report for a completed run ledger.",
    glyph: "E",
  },
  {
    id: "07",
    name: "cbc review-artifact",
    desc: "Read a stored run artifact and export the review as JSON.",
    glyph: "E",
  },
  {
    id: "08",
    name: "cbc review-workspace",
    desc: "Review an arbitrary workspace tree against a task spec, no run required.",
    glyph: "W",
  },
  {
    id: "09",
    name: "cbc ci",
    desc: "CI gate: task + workspace → verdict. Exit code reflects mergeability.",
    glyph: "G",
  },
  {
    id: "10",
    name: "cbc ci-artifact",
    desc: "Recompute a CI gate from a frozen artifact for deterministic audit trails.",
    glyph: "G",
  },
  {
    id: "11",
    name: "cbc trends",
    desc: "Aggregate ledger stats: success rate, avg attempts, cost curves over rolling windows.",
    glyph: "T",
  },
  {
    id: "12",
    name: "cbc benchmark-artifact",
    desc: "Replay a saved benchmark report and re-render the comparison metrics.",
    glyph: "B",
  },
  {
    id: "13",
    name: "cbc api",
    desc: "Start the FastAPI control plane: SSE streams, REST queries, Supabase mirror hook.",
    glyph: "A",
    flags: ["--host", "--port"],
  },
];

export function Capabilities() {
  return (
    <div className="cap-grid">
      {COMMANDS.map((c) => (
        <div className="cap" key={c.id}>
          <div className="cap-head">
            <span className="cap-idx">TOOL · {c.id}</span>
            <span className="cap-glyph">{c.glyph}</span>
          </div>
          <div className="cap-name">{c.name}</div>
          <div className="cap-desc">{c.desc}</div>
          {c.flags && c.flags.length > 0 && (
            <div className="cap-flag">
              {c.flags.map((f) => (
                <span key={f}>{f}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
