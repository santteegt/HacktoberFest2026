// MiniSearch over data/generated/kb.json (text + lead + pageTitle, prefix, fuzzy 0.2) (T2).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import MiniSearch from "minisearch";
import { KbFile } from "../../src/shared/schemas";
import type { KbChunk, KbStats } from "../../src/shared/types";

const KB_PATH = fileURLToPath(new URL("../../data/generated/kb.json", import.meta.url));

interface Index {
  mini: MiniSearch<KbChunk>;
  byId: Map<string, KbChunk>;
  stats: KbStats;
}

let cache: Index | undefined;

function index(): Index {
  if (cache) return cache;
  const parsed = KbFile.safeParse(JSON.parse(readFileSync(KB_PATH, "utf8")));
  if (!parsed.success) throw new Error(`data/generated/kb.json failed validation (run npm run kb:build): ${parsed.error.message}`);
  const kb = parsed.data;
  const mini = new MiniSearch<KbChunk>({
    fields: ["text", "lead", "pageTitle"],
    storeFields: ["id"],
    // The lead is the bold claim of the chunk, so a hit there counts more than a hit in the body.
    searchOptions: { prefix: true, fuzzy: 0.2, boost: { lead: 2, pageTitle: 1.5 }, combineWith: "OR" },
  });
  mini.addAll(kb.chunks);
  cache = {
    mini,
    byId: new Map(kb.chunks.map((c) => [c.id, c])),
    stats: { pages: kb.pages.length, chunks: kb.chunks.length, contentHash: kb.contentHash },
  };
  return cache;
}

export function search(q: string, limit = 3): KbChunk[] {
  const query = q.trim();
  if (!query) return [];
  const { mini, byId } = index();
  return mini
    .search(query)
    .slice(0, Math.max(1, limit))
    .map((hit) => byId.get(hit.id as string))
    .filter((c): c is KbChunk => c !== undefined);
}

export function getChunk(id: string): KbChunk | undefined {
  return index().byId.get(id);
}

export function kbStats(): KbStats {
  return index().stats;
}
