export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-block">
          <strong>System</strong>
          <ul>
            <li>CBC command center</li>
            <li>Python 3.11 · FastAPI</li>
            <li>Next.js 16 · React 19</li>
            <li>Supabase mirror · optional</li>
          </ul>
        </div>
        <div className="footer-block">
          <strong>Reality check</strong>
          <ul>
            <li>
              <span className="ok">● Live status comes from runtime config</span>
            </li>
            <li>
              <span className="ok">● Same-origin API proxy on Vercel</span>
            </li>
            <li>
              <span className="ok">● Structured run detail surface</span>
            </li>
            <li>
              <span className="warn">● Supabase KPIs are optional, not assumed</span>
            </li>
          </ul>
        </div>
        <div className="footer-block">
          <strong>Handles</strong>
          <ul>
            <li>VERIFIED · oracle + suite pass</li>
            <li>FALSIFIED · counterexample found</li>
            <li>TIMED_OUT · wall budget exceeded</li>
            <li>UNPROVEN · inconclusive</li>
          </ul>
        </div>
        <div className="footer-block">
          <strong>Deployment</strong>
          <ul>
            <li>Vercel web edge</li>
            <li>CBC API behind explicit env</li>
            <li>Security headers via vercel.json</li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
