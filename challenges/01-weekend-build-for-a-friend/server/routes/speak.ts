// POST /api/speak (T6): macOS `say` as the fallback text-to-speech. `say` is spawned with an ARGUMENTS ARRAY (never a
// shell string); the previous process is killed on new text or on cancel (POST {cancel:true} or DELETE /api/speak).
import { spawn, type ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";
import { Hono } from "hono";
import { apiError } from "../http";
import { truncateAtSentence } from "../../src/voice/sentences";

export const SAY_BIN = "/usr/bin/say";
export const MAX_SPEAK_CHARS = 600;
/** Voice names: letters, digits and single spaces only (macOS names such as "Samantha" or "Daniel"). */
export const VOICE_RE = /^[A-Za-z0-9]+(?: [A-Za-z0-9]+)*$/;

export type SpeakParse = { ok: true; cancel: true } | { ok: true; cancel: false; text: string; voice?: string; truncated: boolean } | { ok: false; error: string };

/** Validates a request body. Text is cleaned of control characters and cut to MAX_SPEAK_CHARS. */
export function parseSpeakBody(raw: unknown): SpeakParse {
  if (typeof raw !== "object" || raw === null) return { ok: false, error: "body must be a JSON object" };
  const b = raw as Record<string, unknown>;
  if (b.cancel === true) return { ok: true, cancel: true };
  if (typeof b.text !== "string") return { ok: false, error: "text must be a string" };
  // eslint-disable-next-line no-control-regex
  const text = b.text.replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, " ").replace(/\s+/g, " ").trim();
  if (!text) return { ok: false, error: "text is empty" };
  let voice: string | undefined;
  if (b.voice !== undefined && b.voice !== null && b.voice !== "") {
    if (typeof b.voice !== "string" || b.voice.length > 40 || !VOICE_RE.test(b.voice)) {
      return { ok: false, error: "voice may contain only letters, digits and spaces" };
    }
    voice = b.voice;
  }
  const limited = truncateAtSentence(text, MAX_SPEAK_CHARS);
  return { ok: true, cancel: false, text: limited, voice, truncated: limited.length < text.length };
}

/** Arguments for `say`. "--" ends option parsing so text starting with "-" is never read as a flag. */
export function buildSayArgs(text: string, voice?: string): string[] {
  return [...(voice ? ["-v", voice] : []), "--", text];
}

let current: ChildProcess | null = null;

function killCurrent(): boolean {
  const had = !!current && current.exitCode === null && current.signalCode === null;
  if (current && had) current.kill("SIGTERM");
  current = null;
  return had;
}

/** Spawns say; resolves once the process has started, rejects when it cannot be started. */
function startSay(args: string[]): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn(SAY_BIN, args, { stdio: "ignore" }); // args array, no shell
    current = child;
    child.once("spawn", () => resolve());
    child.once("error", (e) => {
      if (current === child) current = null;
      reject(e);
    });
    child.once("exit", () => {
      if (current === child) current = null;
    });
  });
}

const r = new Hono();

r.post("/speak", async (c) => {
  let raw: unknown;
  try {
    raw = await c.req.json();
  } catch {
    return apiError(c, 400, "body must be JSON", "validate");
  }
  const p = parseSpeakBody(raw);
  if (!p.ok) return apiError(c, 400, p.error, "validate");
  if (p.cancel) return c.json({ ok: true, cancelled: killCurrent() });
  if (!existsSync(SAY_BIN)) return apiError(c, 501, "macOS say is not available on this machine", "speak");
  killCurrent();
  try {
    await startSay(buildSayArgs(p.text, p.voice));
  } catch (e) {
    return apiError(c, 500, `could not start say: ${(e as Error).message}`, "speak");
  }
  return c.json({ ok: true, ...(p.truncated ? { truncated: true } : {}) });
});

r.delete("/speak", (c) => c.json({ ok: true, cancelled: killCurrent() }));

export default r;
