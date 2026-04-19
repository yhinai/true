import { Fragment } from "react";

const STAGES: Array<{ title: string; sub: string }> = [
  { title: "Task", sub: "YAML spec" },
  { title: "Plan", sub: "allowed files" },
  { title: "Codex", sub: "generate" },
  { title: "Sandbox", sub: "isolate" },
  { title: "Verify", sub: "oracle + N" },
  { title: "Verdict", sub: "ledger" },
];

export function FlowDiagram() {
  return (
    <div className="flow-panel">
      <div className="flow">
        {STAGES.map((s, i) => (
          <Fragment key={s.title}>
            <div className="flow-node">
              <div className="flow-node-title">{s.title}</div>
              <div className="flow-node-sub">{s.sub}</div>
            </div>
            {i < STAGES.length - 1 && (
              <div className="flow-arrow">
                <span>→</span>
              </div>
            )}
          </Fragment>
        ))}
      </div>
      <div
        style={{
          marginTop: 32,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: 24,
          fontFamily: "var(--font-mono)",
          fontSize: 12,
          color: "var(--text-dim)",
        }}
      >
        <div>
          <div style={{ color: "var(--amber)", fontSize: 10, letterSpacing: "0.2em", marginBottom: 8 }}>
            RETRY LOOP
          </div>
          On FALSIFIED, route_after_verify feeds the counterexample back into the
          next attempt. Bounded by retry_budget.
        </div>
        <div>
          <div style={{ color: "var(--amber)", fontSize: 10, letterSpacing: "0.2em", marginBottom: 8 }}>
            GEARBOX
          </div>
          Parallel candidate fan-out under ConTree sandbox. The gearbox coordinator
          picks the first-verified winner.
        </div>
        <div>
          <div style={{ color: "var(--amber)", fontSize: 10, letterSpacing: "0.2em", marginBottom: 8 }}>
            LEDGER
          </div>
          Every attempt, verify check, and verdict lands in SQLite locally and
          mirrors to Supabase for this dashboard.
        </div>
      </div>
    </div>
  );
}
