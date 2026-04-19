"use client";

import { useEffect, useState } from "react";
import { getSupabase } from "@/lib/supabase";

type Event = {
  id: number;
  run_id: string;
  seq: number;
  kind: string;
  emitted_at: string;
  payload: Record<string, unknown>;
};

export function EventTail() {
  const [events, setEvents] = useState<Event[]>([]);
  const [configured, setConfigured] = useState(true);

  useEffect(() => {
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
  }, []);

  return (
    <div className="panel">
      <div className="panel-head">
        <strong>Event stream</strong>
        <span>
          <span className="dot live" style={{ marginRight: 8 }} />
          REALTIME
        </span>
      </div>
      <div className="events">
        {!configured ? (
          <div className="event-empty">
            Supabase realtime is not configured.
            <br />
            The dashboard can still show runs through the CBC API, but event fan-out
            needs NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.
          </div>
        ) : events.length === 0 ? (
          <div className="event-empty">
            No events yet.
            <br />
            Events stream in as runs progress: attempts, verify checks, verdicts.
          </div>
        ) : (
          events.map((e) => (
            <div key={e.id} className="event">
              <span className="event-time">{formatTime(e.emitted_at)}</span>
              <span className={`event-kind k-${e.kind}`}>{e.kind || "event"}</span>
              <span className="event-body" title={JSON.stringify(e.payload)}>
                {summarize(e)}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
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
  const run = e.run_id.slice(0, 10);
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
