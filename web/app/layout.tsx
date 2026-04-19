import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import { TopBar } from "./components/TopBar";
import { Footer } from "./components/Footer";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display-loaded",
  axes: ["opsz", "SOFT"],
  display: "swap",
  style: ["normal", "italic"],
});

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-sans-loaded",
  display: "swap",
  weight: ["300", "400", "500", "600"],
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono-loaded",
  display: "swap",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "CBC // Command Center",
  description:
    "CBC — Correct by Construction. Verification-first control plane for AI code generation. Deterministic oracles, bounded retries, proof artifacts.",
  openGraph: {
    title: "CBC // Command Center",
    description:
      "Verification-first control plane for AI code generation. Proofs, not promises.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${plex.variable} ${mono.variable}`}>
      <body
        style={{
          fontFamily: "var(--font-sans-loaded), var(--font-sans)",
        }}
      >
        <div className="shell">
          <TopBar />
          <main className="wrap">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
