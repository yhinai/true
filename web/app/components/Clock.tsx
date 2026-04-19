"use client";

import { useEffect, useState } from "react";

export function Clock() {
  const [now, setNow] = useState<string>("--:--:-- UTC");

  useEffect(() => {
    const tick = () => {
      const d = new Date();
      const pad = (n: number) => String(n).padStart(2, "0");
      setNow(
        `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC`
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return <strong suppressHydrationWarning>{now}</strong>;
}
