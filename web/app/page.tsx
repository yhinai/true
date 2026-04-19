import { Hero } from "./components/Hero";
import { PromiseStrip } from "./components/PromiseStrip";
import { KpiRow } from "./components/KpiRow";
import { RunGallery } from "./components/RunGallery";
import { VerdictReel } from "./components/VerdictReel";
import { EventTail } from "./components/EventTail";
import { RemediationFeed } from "./components/RemediationFeed";
import { Capabilities } from "./components/Capabilities";
import { CheckSuite } from "./components/CheckSuite";
import { TaskLibrary } from "./components/TaskLibrary";
import { FlowDiagram } from "./components/FlowDiagram";
import { Section } from "./components/Section";

export default function CommandCenter() {
  return (
    <>
      <Hero />

      <PromiseStrip />

      <Section
        tag="Telemetry — 002"
        title={<><em>Signal</em> floor</>}
        meta="LIVE WHEN CONFIGURED · HONEST WHEN NOT"
        first
      >
        <KpiRow />
      </Section>

      <Section
        id="runs"
        tag="Runs — 003"
        title={<>Every <em>verdict</em> is a proof</>}
        meta="API FIRST · SUPABASE ENRICHMENT WHEN AVAILABLE"
      >
        <RunGallery />
      </Section>

      <VerdictReel />

      <Section
        id="events"
        tag="Stream — 004"
        title={<>Live <em>event</em> tail</>}
        meta="OPTIONAL REALTIME MIRROR"
      >
        <EventTail />
      </Section>

      <Section
        id="remediation"
        tag="Remediation — 005"
        title={<>Agents <em>working</em> for you</>}
        meta="GHA + CODEX + YOLO · AUTONOMOUS CYCLE"
      >
        <RemediationFeed />
      </Section>

      <Section
        id="checks"
        tag="Verification — 005"
        title={<>What a <em>run</em> can prove</>}
        meta="DETERMINISTIC · REPLAYABLE · BOUNDED"
      >
        <CheckSuite />
      </Section>

      <Section
        id="capabilities"
        tag="Capabilities — 006"
        title={<>Tools <em>at hand</em></>}
        meta="CLI · API · REVIEW · BENCHMARK"
      >
        <Capabilities />
      </Section>

      <Section
        id="tasks"
        tag="Library — 007"
        title={<>Task <em>fixtures</em></>}
        meta="REPLAY + LIVE AGENT FIXTURES"
      >
        <TaskLibrary />
      </Section>

      <Section
        id="flow"
        tag="Pipeline — 008"
        title={<>How a <em>task</em> moves</>}
        meta="TASK → PLAN → PATCH → VERIFY → VERDICT"
      >
        <FlowDiagram />
      </Section>
    </>
  );
}
