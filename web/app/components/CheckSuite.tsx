const CHECKS: Array<{ name: string; tag: string; desc: string }> = [
  {
    name: "oracle",
    tag: "core",
    desc: "Task-defined shell/pytest/python command. The authoritative pass/fail.",
  },
  {
    name: "pytest",
    tag: "python",
    desc: "Full test suite runner with structured pass/fail attribution per node.",
  },
  {
    name: "type",
    tag: "python",
    desc: "Type-checker gate (mypy/pyright). Optional, configurable command.",
  },
  {
    name: "lint",
    tag: "python",
    desc: "Syntax/compile check via compileall by default; pluggable linter command.",
  },
  {
    name: "coverage",
    tag: "python",
    desc: "Coverage threshold gate. Rejects regressions below the configured floor.",
  },
  {
    name: "mutation",
    tag: "python",
    desc: "Mutation testing. Injects faults, demands the test suite catches them.",
  },
  {
    name: "crosshair",
    tag: "symbolic",
    desc: "Symbolic execution via CrossHair. Surfaces counterexamples from contracts.",
  },
  {
    name: "hypothesis",
    tag: "property",
    desc: "Property-based testing. Generative counterexamples with shrinking.",
  },
  {
    name: "structural",
    tag: "meta",
    desc: "File tree and schema shape validation. Catches drift before semantics.",
  },
];

export function CheckSuite() {
  return (
    <div className="check-grid">
      {CHECKS.map((c) => (
        <div className="check" key={c.name}>
          <div className="check-name">
            {c.name}
            <span className="dot" />
          </div>
          <div className="check-desc">{c.desc}</div>
          <div className="check-tag">{c.tag}</div>
        </div>
      ))}
    </div>
  );
}
