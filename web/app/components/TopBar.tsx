import Link from "next/link";
import { Clock } from "./Clock";

export function TopBar() {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <div className="brand">
          <span className="brand-mark">C</span>
          <span className="brand-name">CBC</span>
          <span className="brand-divider">/</span>
          <span className="brand-tag">COMMAND CENTER</span>
        </div>

        <div className="topbar-status">
          <span>
            <span className="dot live" />
            <strong>SAME-ORIGIN API</strong>
          </span>
          <span>
            T— <Clock />
          </span>
          <span>
            ROUTE <strong>/api/cbc</strong>
          </span>
        </div>

        <nav className="topbar-nav">
          <Link href="#runs">Runs</Link>
          <Link href="#checks">Checks</Link>
          <Link href="#capabilities">Tools</Link>
          <Link href="#tasks">Library</Link>
          <Link href="#flow">Flow</Link>
        </nav>
      </div>
    </header>
  );
}
