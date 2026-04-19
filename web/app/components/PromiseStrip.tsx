const PROMISES = [
  {
    kicker: "00",
    strike: "Code review",
    tail: "Every patch runs the full oracle suite before it lands.",
  },
  {
    kicker: "01",
    strike: "Merge conflicts",
    tail: "PR-gated push-forward auto-rebases and resolves safe classes.",
  },
  {
    kicker: "02",
    strike: "Broken tests",
    tail: "No VERIFIED verdict, no merge. The gate is deterministic.",
  },
  {
    kicker: "03",
    strike: "Time wasted debugging",
    tail: "Failure context feeds the next attempt — bounded, then aborted.",
  },
];

export function PromiseStrip() {
  return (
    <section className="promise" aria-labelledby="promise-title">
      <div className="promise-head">
        <div className="promise-kicker">The promise — 00</div>
        <h2 id="promise-title" className="promise-title">
          Four things you&rsquo;ll <em>never</em> do again.
        </h2>
      </div>
      <div className="promise-grid">
        {PROMISES.map((p) => (
          <article key={p.kicker} className="promise-card">
            <div className="promise-index">No. {p.kicker}</div>
            <div className="promise-line">
              <span className="promise-no">No</span>
              <span className="promise-strike">{p.strike}</span>
            </div>
            <p className="promise-tail">{p.tail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
