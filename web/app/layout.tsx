import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CBC — Correct by Construction",
  description: "Live ledger viewer for CBC run verdicts.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <strong>CBC</strong>
          <span className="muted">Correct by Construction · live ledger</span>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
