type Verdict = {
  label: "VERIFIED" | "FALSIFIED" | "TIMED_OUT" | "UNPROVEN";
  runId: string;
};

const DEFAULT_VERDICTS: Verdict[] = [
  { label: "VERIFIED", runId: "a1f2c3d" },
  { label: "FALSIFIED", runId: "b7c8d9e" },
  { label: "VERIFIED", runId: "c2e3f4a" },
  { label: "VERIFIED", runId: "d5a6b7c" },
  { label: "TIMED_OUT", runId: "e8f9a0b" },
  { label: "VERIFIED", runId: "f1b2c3d" },
  { label: "UNPROVEN", runId: "a4b5c6d" },
  { label: "VERIFIED", runId: "b7e8f9a" },
];

function verdictClass(v: Verdict["label"]): string {
  switch (v) {
    case "VERIFIED":
      return "verdict-stamp verdict-ok";
    case "FALSIFIED":
      return "verdict-stamp verdict-bad";
    case "TIMED_OUT":
      return "verdict-stamp verdict-warn";
    case "UNPROVEN":
      return "verdict-stamp verdict-dim";
  }
}

export function VerdictReel({ verdicts = DEFAULT_VERDICTS }: { verdicts?: Verdict[] }) {
  const loops = [0, 1];
  return (
    <section className="verdict-reel" aria-label="Recent verdicts">
      <div className="verdict-reel-rule verdict-reel-rule-top" aria-hidden />
      <div className="verdict-reel-track">
        {loops.map((loop) => (
          <div className="verdict-reel-group" key={loop} aria-hidden={loop === 1}>
            {verdicts.map((v, i) => (
              <span className={verdictClass(v.label)} key={`${loop}-${i}`}>
                <span className="verdict-stamp-label">{v.label}</span>
                <sup className="verdict-stamp-id">#{v.runId}</sup>
                <span className="verdict-stamp-sep" aria-hidden>·</span>
              </span>
            ))}
          </div>
        ))}
      </div>
      <div className="verdict-reel-rule verdict-reel-rule-bot" aria-hidden />
    </section>
  );
}
