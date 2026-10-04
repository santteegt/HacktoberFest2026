// Small HTTP helpers shared by route modules. FROZEN (T0; only T7/T10 edit).
import type { Context } from "hono";
import type { ContentfulStatusCode } from "hono/utils/http-status";
import type { z } from "zod";
import type { ApiError } from "../src/shared/types";

/** Error response in the contract shape `{ error, stage? }`. */
export const apiError = (c: Context, status: ContentfulStatusCode, error: string, stage?: string) =>
  c.json<ApiError>(stage ? { error, stage } : { error }, status);

/** 501 for routes whose owner task has not landed yet. */
export const notImplemented = (stage: string) => (c: Context) => apiError(c, 501, "not implemented", stage);

/** Parse a JSON body with a zod schema; returns the data or a 400 Response. */
export async function parseBody<T extends z.ZodType>(
  c: Context,
  schema: T,
): Promise<{ ok: true; data: z.infer<T> } | { ok: false; res: Response }> {
  let raw: unknown;
  try {
    raw = await c.req.json();
  } catch {
    return { ok: false, res: apiError(c, 400, "body must be JSON", "validate") };
  }
  const r = schema.safeParse(raw);
  if (!r.success) return { ok: false, res: apiError(c, 400, r.error.message, "validate") };
  return { ok: true, data: r.data };
}
