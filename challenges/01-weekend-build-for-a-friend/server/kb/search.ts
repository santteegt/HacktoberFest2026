// MiniSearch over data/generated/kb.json (text + lead + pageTitle) (T2; stopwords, prefix rule and domain
// vocabulary added by T11). Pure functions: no model call, no network.
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

// ---------- generic text handling ----------

/**
 * Function words that carry no topic. Dropped at index time and at query time, so "what does droop do" searches
 * for "droop" alone. Deliberately NOT here: up, out, off, over, left, right, front, rear, more (domain words
 * such as "up-stops" and "rear grip" depend on them being searchable).
 */
export const STOPWORDS: ReadonlySet<string> = new Set(
  (
    "a about am an and are as at be been but by can could did do does for from get had has have how i if in into is it its " +
    "just me much many my of on or our should so than that the their then there these they this those to was we were what " +
    "when where which who why will with would you your"
  ).split(/\s+/),
);

/** Terms of this length or shorter are matched exactly: "do" must not be a prefix of "droop", "drive" or "downforce". */
export const MAX_EXACT_ONLY_LENGTH = 3;
/** True when a query term may also match longer words that start with it ("stiff" finds "stiffer"). */
export const usesPrefix = (term: string): boolean => term.length > MAX_EXACT_ONLY_LENGTH;

// ---------- domain vocabulary (the only hand-made part; keep it small and plainly justified) ----------

/**
 * Spelling variants: the notes are written in American English, drivers in a mix. Applied at index and query time.
 */
const SPELLING: Readonly<Record<string, string>> = {
  tyre: "tire",
  tyres: "tires",
  centre: "center",
};

/**
 * Driver words for things the notes name differently. Applied to the QUERY only, as extra OR terms next to the
 * original word. Multi-word keys are matched as phrases first. Every entry says where the gap came from.
 */
const SYNONYMS: ReadonlyArray<readonly [phrase: string, extra: string]> = [
  ["final drive ratio", "fdr gearing"], // drivers spell it out; the drivetrain page says FDR and "gearing"
  ["grip", "traction"], // drivers say grip, the notes' pages and headings say traction
];

/** Lower-case, word-split, stopword-free terms of a query, with spelling variants applied. */
export function queryTerms(q: string): string[] {
  return q
    .toLowerCase()
    .split(/[^\p{L}\p{N}]+/u)
    .filter(Boolean)
    .map((t) => SPELLING[t] ?? t)
    .filter((t) => t.length > 1 && !STOPWORDS.has(t));
}

/** Query text sent to MiniSearch: the content terms plus any domain-vocabulary extras. */
export function expandQuery(q: string): string {
  const lower = ` ${q.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim()} `;
  const extras = SYNONYMS.filter(([phrase]) => lower.includes(` ${phrase} `)).map(([, extra]) => extra);
  return [...queryTerms(q), ...extras].join(" ");
}

/** MiniSearch term processor for indexing AND searching: lower-case, spelling variant, stopwords dropped. */
function processTerm(term: string): string | null {
  const t = term.toLowerCase();
  if (t.length < 2 || STOPWORDS.has(t)) return null;
  return SPELLING[t] ?? t;
}

function index(): Index {
  if (cache) return cache;
  const parsed = KbFile.safeParse(JSON.parse(readFileSync(KB_PATH, "utf8")));
  if (!parsed.success) throw new Error(`data/generated/kb.json failed validation (run npm run kb:build): ${parsed.error.message}`);
  const kb = parsed.data;
  const mini = new MiniSearch<KbChunk>({
    fields: ["text", "lead", "pageTitle"],
    storeFields: ["id"],
    processTerm,
    // The lead is the bold claim of the chunk, so a hit there counts more than a hit in the body.
    // Prefix matching only for terms longer than 3 characters (see MAX_EXACT_ONLY_LENGTH).
    searchOptions: {
      prefix: usesPrefix,
      fuzzy: 0.2,
      boost: { lead: 2, pageTitle: 1.5 },
      combineWith: "OR",
    },
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
  const query = expandQuery(q);
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
