"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { getSupabase } from "@/lib/supabase";

type Event = {
  id: number | string;
  run_id: string;
  seq: number;
  kind: string;
  emitted_at: string;
  payload: Record<string, unknown>;
};

const DEMO_EVENTS: Event[] = [
  {
    id: "demo-1",
    run_id: "run_a1f2c3d4e5",
    seq: 1,
    kind: "PLAN",
    emitted_at: new Date(Date.now() - 18000).toISOString(),
    payload: { goal: "fix calculator overflow branch" },
  },
  {
    id: "demo-2",
    run_id: "run_a1f2c3d4e5",
    seq: 2,
    kind: "CODE",
    emitted_at: new Date(Date.now() - 15000).toISOString(),
    payload: { files: 2, bytes: 1824 },
  },
  {
    id: "demo-3",
    run_id: "run_a1f2c3d4e5",
    seq: 3,
    kind: "VERIFY",
    emitted_at: new Date(Date.now() - 9000).toISOString(),
    payload: { suite: "pytest", tests: 249 },
  },
  {
    id: "demo-4",
    run_id: "run_a1f2c3d4e5",
    seq: 4,
    kind: "VERIFIED",
    emitted_at: new Date(Date.now() - 4000).toISOString(),
    payload: { all_green: true },
  },
  {
    id: "demo-5",
    run_id: "run_b7c8d9e0f1",
    seq: 1,
    kind: "FALSIFIED",
    emitted_at: new Date(Date.now() - 1000).toISOString(),
    payload: { reason: "property counter-example" },
  },
];

export function EventTail({ events: propEvents }: { events?: Event[] } = {}) {
  const [events, setEvents] = useState<Event[]>(propEvents ?? []);
  const [configured, setConfigured] = useState(true);
  const [demoIdx, setDemoIdx] = useState(0);
  const reducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    if (propEvents) return;
    const sb = getSupabase();
    if (!sb) {
      setConfigured(false);
      return;
    }
    let cancelled = false;

    (async () => {
      const { data, error } = await sb
        .from("cbc_run_events")
        .select("id, run_id, seq, kind, emitted_at, payload")
        .order("emitted_at", { ascending: false })
        .limit(60);
      if (!cancelled && !error && data) setEvents(data as Event[]);
    })();

    const channel = sb
      .channel("cbc_run_events_live")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "cbc_run_events" },
        (payload: { new: Event }) => {
          if (cancelled) return;
          setEvents((prev) => [payload.new, ...prev].slice(0, 60));
        }
      )
      .subscribe();

    return () => {
      cancelled = true;
      sb.removeChannel(channel);
    };
  }, [propEvents]);

  // Demo loop: if not configured and no real events, cycle scripted demo rows.
  const useDemo = !configured && events.length === 0;
  useEffect(() => {
    if (!useDemo) return;
    setDemoIdx(0);
    const t = setInterval(() => {
      setDemoIdx((i) => (i + 1) % (DEMO_EVENTS.length + 2));
    }, 2200);
    return () => clearInterval(t);
  }, [useDemo]);

  const displayEvents = useMemo<Event[]>(() => {
    if (useDemo) return DEMO_EVENTS.slice(0, Math.min(demoIdx + 1, DEMO_EVENTS.length));
    return events;
  }, [useDemo, demoIdx, events]);

  return (
    <div className="panel printer">
      <div className="printer-perf" aria-hidden />
      <div className="panel-head">
        <strong>Event stream</strong>
        <span>
          <span className="dot live heartbeat" style={{ marginRight: 8 }} />
          {useDemo ? "DEMO LOOP" : "REALTIME"}
        </span>
      </div>
      <div className="events printer-paper">
        {displayEvents.length === 0 ? (
          <div className="event-empty">
            {configured ? (
              <>
                No events yet.
                <br />
                Events stream in as runs progress: attempts, verify checks, verdicts.
              </>
            ) : (
              <>
                Supabase realtime is not configured.
                <br />
                Showing scripted demo trace. Provide NEXT_PUBLIC_SUPABASE_URL + ANON_KEY to go live.
              </>
            )}
          </div>
        ) : (
          displayEvents.map((e, idx) => (
            <PrinterRow
              key={`${e.id}-${idx}`}
              event={e}
              animate={!reducedMotion && (useDemo ? idx === displayEvents.length - 1 : idx === 0)}
            />
          ))
        )}
        <div className="printer-cursor-row" aria-hidden>
          <span className="printer-cursor">▌</span>
        </div>
      </div>
    </div>
  );
}

function PrinterRow({ event, animate }: { event: Event; animate: boolean }) {
  const line = useMemo(() => buildLine(event), [event]);
  const kindClass = kindToClass(event.kind);
  // Typing duration proportional to length, ~28ms/char.
  const steps = line.body.length || 1;
  const duration = Math.min(1400, Math.max(240, steps * 28));
  const style = animate
    ? ({
        // CSS custom properties consumed by .event-body.typing
        ["--steps" as const]: String(steps),
        ["--duration" as const]: `${duration}ms`,
      } as React.CSSProperties)
    : undefined;

  return (
    <div className="event printer-row">
      <span className="event-time">{line.time}</span>
      <span className={`event-kind ${kindClass}`}>{line.kind}</span>
      <span
        className={`event-body${animate ? " typing" : ""}`}
        style={style}
        title={JSON.stringify(event.payload)}
      >
        {line.body}
      </span>
    </div>
  );
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  const mqRef = useRef<MediaQueryList | null>(null);
  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    mqRef.current = mq;
    setReduced(mq.matches);
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);
  return reduced;
}

function kindToClass(kind: string): string {
  const k = (kind || "").toUpperCase();
  if (k === "VERIFIED") return "k-verified";
  if (k === "FALSIFIED") return "k-falsified";
  if (k === "TIMED_OUT" || k === "TIMEOUT") return "k-timed";
  if (k === "VERIFY") return "k-verify";
  if (k === "PLAN" || k === "CODE" || k === "ATTEMPT") return "k-plan";
  if (k === "VERDICT") return "k-verdict";
  if (k === "STDOUT") return "k-stdout";
  return "";
}

function buildLine(e: Event): { time: string; kind: string; body: string } {
  return {
    time: formatTime(e.emitted_at),
    kind: (e.kind || "event").toUpperCase(),
    body: summarize(e),
  };
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
  } catch {
    return "--:--:--";
  }
}

function summarize(e: Event): string {
  const p = e.payload || {};
  const run = (e.run_id || "").slice(0, 10);
  const keys = Object.keys(p).slice(0, 3);
  if (keys.length === 0) return `run ${run} · seq ${e.seq}`;
  const snippet = keys
    .map((k) => `${k}=${stringify((p as Record<string, unknown>)[k])}`)
    .join(" ");
  return `${run} · ${snippet}`;
}

function stringify(v: unknown): string {
  if (typeof v === "string") return v.length > 40 ? v.slice(0, 40) + "…" : v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (v == null) return "∅";
  return "{…}";
}
