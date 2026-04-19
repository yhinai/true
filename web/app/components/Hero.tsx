import Link from "next/link";
import { RuntimeStatus } from "./RuntimeStatus";

export function Hero() {
  return (
    <section className="hero">
      <div className="hero-head">
        <div>
          <div className="hero-label">Mission brief — 001</div>
          <h1 className="hero-title">
            Proofs,<br />
            <em>not</em> <span className="ghost">promises.</span>
          </h1>
        </div>
        <div className="hero-lead">
          <strong>CBC</strong> is a verification-first control plane for AI code
          generation. Every attempt is sandboxed, every claim is checked, every
          verdict is reproducible. No &ldquo;looks good to me.&rdquo;
        </div>
      </div>

      <div className="hero-grid">
        <div className="hero-panel hero-panel-primary">
          <div className="hero-panel-kicker">Operator focus</div>
          <h2>Watch runs, inspect verdicts, and verify the wiring before you trust the dashboard.</h2>
          <p>
            This surface now prefers honest fallbacks: same-origin API proxying,
            explicit Supabase status, and structured run details instead of fake
            “online” theater.
          </p>
          <div className="hero-actions">
            <Link href="#runs" className="hero-action hero-action-primary">
              Open live runs
            </Link>
            <Link href="#checks" className="hero-action">
              Inspect checks
            </Link>
            <Link href="#tasks" className="hero-action">
              Browse fixtures
            </Link>
          </div>
        </div>

        <div className="hero-panel">
          <div className="hero-panel-kicker">Quickstart</div>
          <div className="command-stack">
            <div className="command-card">
              <span>Replay demo</span>
              <code>./scripts/run_compare.sh</code>
            </div>
            <div className="command-card">
              <span>Run one task</span>
              <code>uv run cbc run fixtures/oracle_tasks/calculator_bug/task.yaml</code>
            </div>
            <div className="command-card">
              <span>Zero-config solve</span>
              <code>uv run cbc solve "Fix the failing tests" --json</code>
            </div>
          </div>
        </div>
      </div>

      <RuntimeStatus />
    </section>
  );
}
