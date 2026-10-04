// Session bundle state shared by the Session and Setup screens (T4b). Writes the app-wide `session` and
// `currentSetup` signals from the store after each server call.
import { signal } from "@preact/signals";
import { request } from "../../api/client";
import type { SessionBundle } from "../../shared/api";
import type { Setup } from "../../shared/types";
import { currentSetup, session } from "../store";

/** GET /api/sessions/:id for the open session: runs, changes and every setup row it references. */
export const bundle = signal<SessionBundle | null>(null);
export const bundleError = signal<string | null>(null);

function apply(b: SessionBundle): void {
  bundle.value = b;
  session.value = b.session;
  currentSetup.value = b.setups.find((s) => s.id === b.session.currentSetupId) ?? currentSetup.value;
}

/** Opens a session by id (loads the bundle and updates the app-wide signals). */
export async function openSession(id: string): Promise<SessionBundle> {
  const b = await request("GET /api/sessions/:id", undefined, { params: { id } });
  bundleError.value = null;
  apply(b);
  return b;
}

/** Reloads the open session's bundle; no-op without an open session. */
export async function refreshBundle(): Promise<SessionBundle | null> {
  const id = session.value?.id;
  if (!id) return null;
  try {
    return await openSession(id);
  } catch (e) {
    bundleError.value = e instanceof Error ? e.message : String(e);
    return null;
  }
}

/**
 * Loads the bundle for the app's open session (used when a screen mounts). Always re-fetches (T7): the coach
 * screen writes changes and outcomes through its own calls, so a cached bundle would hide them here.
 */
export async function ensureBundle(): Promise<void> {
  if (!session.value?.id) return;
  await refreshBundle();
}

export function setupById(id: string): Setup | undefined {
  return bundle.value?.setups.find((s) => s.id === id);
}
