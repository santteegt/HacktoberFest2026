// Held-out retrieval check (T11). Same metric as eval-retrieval.ts (hit = any accepted chunk id in the top 3),
// on the 10 questions in data/eval/retrieval-heldout.json that were NOT used to design the search fixes.
//
//   npx tsx scripts/eval-retrieval-heldout.ts                 (new search, held-out set)
//   SET=original npx tsx scripts/eval-retrieval-heldout.ts    (the 20 design questions instead)
//   SEARCH_MODULE=/abs/path/to/old-search.ts ...              (run another copy of search.ts, e.g. the committed one, for old-vs-new)
// Exit code 0 always (this is a measurement, not a gate); the summary is printed as JSON on stdout.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const here = (p: string) => fileURLToPath(new URL(p, import.meta.url));
const SET = process.env.SET === "original" ? "original" : "heldout";
const file = SET === "original" ? "../data/eval/retrieval-questions.json" : "../data/eval/retrieval-heldout.json";
interface Q {
  id: string;
  question: string;
  accept: string[];
}
const { questions } = JSON.parse(readFileSync(here(file), "utf8")) as { questions: Q[] };
const mod = (await import(process.env.SEARCH_MODULE ?? "../server/kb/search")) as typeof import("../server/kb/search");

const missingIds = questions.flatMap((q) => q.accept.filter((id) => !mod.getChunk(id)).map((id) => ({ question: q.id, id })));
const rows = questions.map((q) => {
  const returned = mod.search(q.question, 3).map((c) => c.id);
  const rank = returned.findIndex((id) => q.accept.includes(id));
  return { id: q.id, question: q.question, hit: rank >= 0, rank: rank >= 0 ? rank + 1 : null, accept: q.accept, returned };
});
for (const r of rows) console.error(`${r.hit ? "hit " : "MISS"} ${r.id} ${r.question}${r.hit ? `  (rank ${r.rank})` : ""}`);
const hits = rows.filter((r) => r.hit).length;
console.log(
  JSON.stringify(
    {
      date: new Date().toISOString(),
      set: SET,
      searchModule: process.env.SEARCH_MODULE ?? "server/kb/search.ts",
      questions: rows.length,
      hits,
      hitPct: Math.round((hits / rows.length) * 1000) / 10,
      acceptedIdsMissingFromKb: missingIds,
      misses: rows.filter((r) => !r.hit).map(({ id, question, accept, returned }) => ({ id, question, accept, returned })),
    },
    null,
    2,
  ),
);
