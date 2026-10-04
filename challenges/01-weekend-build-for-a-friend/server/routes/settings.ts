// GET/PUT /api/settings (T1). Defaults come from server/config.ts; PUT accepts any subset and returns the full settings.
import { Hono } from "hono";
import { parseBody } from "../http";
import { PutSettingsBody } from "../../src/shared/api";
import { getSettings, putSettings } from "../vault/repo";

const r = new Hono();
r.get("/settings", async (c) => c.json(await getSettings()));
r.put("/settings", async (c) => {
  const b = await parseBody(c, PutSettingsBody);
  if (!b.ok) return b.res;
  return c.json(await putSettings(b.data));
});

export default r;
