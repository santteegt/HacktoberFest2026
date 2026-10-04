// Shared settings-screen state (T4c): saving through PUT /api/settings and the live probes that the Voice and About
// sections both show. Nothing here claims offline voice works: it only reports what the browser says about itself.
import { signal } from "@preact/signals";
import { putSettings } from "../../api/client";
import type { Settings } from "../../shared/types";
import { getSpeechInputStatus, listLocalVoices } from "../../voice";
import type { SpeechInputStatus, VoiceChoice } from "../../voice";
import { settings } from "../store";

export function errText(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}

/** PUT a partial settings object and mirror the server's answer into the app-wide `settings` signal. */
export async function saveSettings(patch: Parameters<typeof putSettings>[0]): Promise<Settings> {
  const next = await putSettings(patch);
  settings.value = next;
  return next;
}

/** Live status of the speech input for the mode currently chosen. */
export const speechStatus = signal<SpeechInputStatus | null>(null);
/** What the browser says about on-device recognition, whatever mode is chosen (for the offline checklist). */
export const localProbe = signal<SpeechInputStatus | null>(null);
export const localVoices = signal<VoiceChoice[] | null>(null);

export async function refreshSpeechStatus(mode: Settings["voiceIn"]): Promise<void> {
  try {
    speechStatus.value = await getSpeechInputStatus(mode);
  } catch (e) {
    speechStatus.value = { mode, state: "unavailable", onDeviceReady: false, detail: `Status check failed: ${errText(e)}` };
  }
}

export async function refreshLocalProbe(): Promise<void> {
  try {
    localProbe.value = await getSpeechInputStatus("local");
  } catch {
    localProbe.value = null;
  }
}

export async function refreshVoices(): Promise<void> {
  try {
    localVoices.value = await listLocalVoices();
  } catch {
    localVoices.value = [];
  }
}
