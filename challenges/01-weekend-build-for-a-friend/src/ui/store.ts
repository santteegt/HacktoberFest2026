// App-wide state as Preact signals. Created by T0; T4a owns it from here.
// Screens read these signals; only src/api/client.ts results should be written into them.
import { signal } from "@preact/signals";
import type { MetaResponse } from "../shared/api";
import type { LlmStatus, Session, Settings, Setup } from "../shared/types";

export const ROUTES = ["coach", "setup", "session", "race", "settings"] as const;
export type Route = (typeof ROUTES)[number];

/** GET /api/meta: params, symptoms, levers, prechecks, kbStats. Null until loaded. */
export const meta = signal<MetaResponse | null>(null);
/** GET /api/settings. Null until loaded. */
export const settings = signal<Settings | null>(null);
/** The open practice session, if any. */
export const session = signal<Session | null>(null);
/** The session's current setup row (session.currentSetupId). */
export const currentSetup = signal<Setup | null>(null);
/** GET /api/llm/status, polled by the top bar. */
export const llmStatus = signal<LlmStatus | null>(null);
/** Current screen, mirrored from location.hash ("#/setup" -> "setup"). */
export const route = signal<Route>(routeFromHash(typeof location === "undefined" ? "" : location.hash));

export function routeFromHash(hash: string): Route {
  const name = hash.replace(/^#\/?/, "").split(/[/?]/)[0];
  return (ROUTES as readonly string[]).includes(name) ? (name as Route) : "coach";
}

export function navigate(to: Route): void {
  location.hash = `#/${to}`;
}

/** Keeps `route` in sync with location.hash; returns an unsubscribe function. */
export function startHashRouter(): () => void {
  const sync = () => {
    route.value = routeFromHash(location.hash);
  };
  addEventListener("hashchange", sync);
  sync();
  return () => removeEventListener("hashchange", sync);
}
