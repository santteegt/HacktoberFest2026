// Global citation drawer state (T4a). Any screen can call openCitation(chunkId); <DrawerHost/> (mounted once in App) shows it.
import { signal } from "@preact/signals";

export const openId = signal<string | null>(null);

export function openCitation(chunkId: string): void {
  openId.value = chunkId;
}
export function closeCitation(): void {
  openId.value = null;
}
