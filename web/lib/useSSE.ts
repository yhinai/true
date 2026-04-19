"use client";

import { useEffect, useRef, useState } from "react";

export type SSEState<T> = {
  data: T | null;
  event: string | null;
  connected: boolean;
  error: string | null;
};

/**
 * Subscribe to a Server-Sent Events endpoint. The last frame wins; we keep a
 * tiny API surface so pages can render whatever the backend sent last.
 */
export function useSSE<T>(url: string | null, eventFilter?: string[]): SSEState<T> {
  const [state, setState] = useState<SSEState<T>>({
    data: null,
    event: null,
    connected: false,
    error: null,
  });
  const filterRef = useRef(eventFilter);
  filterRef.current = eventFilter;

  useEffect(() => {
    if (!url) return;
    const es = new EventSource(url);
    setState((s) => ({ ...s, connected: true, error: null }));

    const handle = (ev: MessageEvent, name: string) => {
      const filter = filterRef.current;
      if (filter && !filter.includes(name)) return;
      try {
        const data = JSON.parse(ev.data) as T;
        setState({ data, event: name, connected: true, error: null });
      } catch (err) {
        setState((s) => ({ ...s, error: String(err) }));
      }
    };
    const events = ["snapshot", "update", "done", "error", "runs"];
    const listeners: Array<[string, (ev: MessageEvent) => void]> = events.map((n) => {
      const l = (ev: MessageEvent) => handle(ev, n);
      es.addEventListener(n, l as EventListener);
      return [n, l];
    });
    es.onerror = () => setState((s) => ({ ...s, connected: false }));

    return () => {
      listeners.forEach(([n, l]) => es.removeEventListener(n, l as EventListener));
      es.close();
    };
  }, [url]);

  return state;
}
