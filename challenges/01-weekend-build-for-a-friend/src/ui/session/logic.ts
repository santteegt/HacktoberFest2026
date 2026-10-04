// Pure helpers for the Session screen (T4b). No DOM or Preact imports so vitest can run them in node.

export interface LapParse {
  /** Lap times in milliseconds, in the order given. */
  laps: number[];
  /** Tokens that were not a lap time. */
  bad: string[];
}

/** One time token: "14.9", "14,9" is NOT supported (comma separates laps), "1:14.9" = 74.9 s. Returns ms or null. */
export function parseOneLap(token: string): number | null {
  const t = token.trim();
  if (!t) return null;
  let sec: number;
  const m = /^(\d+):(\d{1,2}(?:\.\d+)?)$/.exec(t);
  if (m) sec = Number(m[1]) * 60 + Number(m[2]);
  else if (/^\d+(\.\d+)?$|^\.\d+$/.test(t)) sec = Number(t);
  else return null;
  if (!Number.isFinite(sec) || sec <= 0 || sec > 600) return null;
  return Math.round(sec * 1000);
}

/** Pasted lap times: seconds separated by whitespace, commas or semicolons. "14.9 15.1, 14.8" -> [14900,15100,14800]. */
export function parseLapTimes(text: string): LapParse {
  const laps: number[] = [];
  const bad: string[] = [];
  for (const tok of text.split(/[\s,;]+/)) {
    if (!tok) continue;
    const ms = parseOneLap(tok);
    if (ms === null) bad.push(tok);
    else laps.push(ms);
  }
  return { laps, bad };
}

/** 14900 -> "14.90". */
export function formatLap(ms: number | undefined): string {
  if (ms === undefined || ms === null) return "-";
  return (ms / 1000).toFixed(2);
}

export function bestOf(laps: number[]): number | undefined {
  return laps.length ? Math.min(...laps) : undefined;
}

export function today(d = new Date()): string {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function timeOfDayLabel(ts: number): string {
  const d = new Date(ts);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())}`;
}

/** Next value of the tyre-runs counter: current + 1, treating an unset counter as 0. */
export function nextTyreRuns(current: unknown): number {
  return (typeof current === "number" && Number.isFinite(current) ? current : 0) + 1;
}
