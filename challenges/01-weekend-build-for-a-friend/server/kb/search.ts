// MiniSearch over data/generated/kb.json (text + lead + pageTitle, prefix, fuzzy 0.2) (T2). T0 stub.
import type { KbChunk, KbStats } from "../../src/shared/types";

export function search(_q: string, _limit = 3): KbChunk[] {
  throw new Error("not implemented");
}
export function getChunk(_id: string): KbChunk | undefined {
  throw new Error("not implemented");
}
export function kbStats(): KbStats {
  throw new Error("not implemented");
}
