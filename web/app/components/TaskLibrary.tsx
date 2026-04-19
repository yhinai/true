const TASKS: Array<{
  id: string;
  lang: "python" | "shell" | "javascript" | "text" | "json";
  desc: string;
  live?: boolean;
}> = [
  { id: "calculator_bug", lang: "python", desc: "Fix addition in calculator.py" },
  { id: "calculator_bug_codex", lang: "python", desc: "Same, with live Codex", live: true },
  { id: "live_codex_calculator", lang: "python", desc: "Alternate live-Codex calculator fixture", live: true },
  {
    id: "checkout_tax_propagation",
    lang: "python",
    desc: "Propagate a taxed total signature across pricing and checkout",
  },
  {
    id: "greeting_text_patch",
    lang: "text",
    desc: "Single-line greeting typo fix (golden fixture)",
  },
  {
    id: "json_status_rollup",
    lang: "json",
    desc: "Repair a derived JSON summary (derived-state, golden)",
  },
  {
    id: "price_format_property_regression",
    lang: "python",
    desc: "Fix price formatting and emit a regression artifact from a property case",
  },
  {
    id: "shell_banner_contract",
    lang: "shell",
    desc: "Repair a shell-based verification banner (stdout + exit code contract)",
  },
  { id: "slug_shell_bug", lang: "shell", desc: "Fix slug rendering for shell validator" },
  { id: "slug_shell_bug_codex", lang: "shell", desc: "Same, with live Codex", live: true },
  {
    id: "slugify_property_regression",
    lang: "python",
    desc: "Fix slugify and capture a regression test from a failing property case",
  },
  {
    id: "slugify_property_regression_codex",
    lang: "python",
    desc: "Same, with live Codex",
    live: true,
  },
  {
    id: "status_badge_js_contract",
    lang: "javascript",
    desc: "Repair JS status badge labels (via Node)",
  },
  { id: "title_case_bug", lang: "python", desc: "Fix title casing helper" },
  { id: "title_case_bug_codex", lang: "python", desc: "Same, with live Codex", live: true },
];

export function TaskLibrary() {
  return (
    <div className="task-grid">
      {TASKS.map((t) => (
        <div className="task" key={t.id}>
          <div className="task-row">
            <div className="task-name">{t.id}</div>
            <div className={`task-lang ${t.lang}`}>{t.lang}</div>
          </div>
          <div className="task-desc">{t.desc}</div>
          <div className="task-meta">
            <span>REPLAY</span>
            {t.live && <span className="live">◆ LIVE CODEX</span>}
          </div>
        </div>
      ))}
    </div>
  );
}
