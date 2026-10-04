// POST /api/speak (T6): macOS `say` fallback TTS. Spawn with an args array (never a shell string);
// kill the previous process on new text. T0 stub: 501 until T6 lands.
import { Hono } from "hono";
import { notImplemented } from "../http";

const r = new Hono();
r.post("/speak", notImplemented("speak"));

export default r;
