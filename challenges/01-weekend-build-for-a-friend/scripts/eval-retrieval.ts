// Top-3 retrieval hit rate of the KB search (T9; plan 8.1). Runs the real MiniSearch index
// (server/kb/search.ts) on the 20 questions in data/eval/retrieval-questions.json.
// hit = any accepted chunk id in the top 3. Pass threshold 85% (memory decision).
// Run `npm run kb:build` first; every accepted id is checked against data/generated/kb.json.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { getChunk, kbStats, search } from "../server/kb/search";

const THRESHOLD = 85;
const here = (p: string) => fileURLToPath(new URL(p, import.meta.url));
interface Q {
  id: string;
  question: string;
  accept: string[];
}
const { questions } = JSON.parse(readFileSync(here("../data/eval/retrieval-questions.json"), "utf8")) as { questions: Q[] };

const missingIds = questions.flatMap((q) => q.accept.filter((id) => !getChunk(id)).map((id) => ({ question: q.id, id })));

const rows = questions.map((q) => {
  const top = search(q.question, 3).map((c) => c.id);
  const rank = top.findIndex((id) => q.accept.includes(id));
  return { id: q.id, question: q.question, hit: rank >= 0, rank: rank >= 0 ? rank + 1 : null, accept: q.accept, returned: top };
});
for (const r of rows) console.error(`${r.hit ? "hit " : "MISS"} ${r.id} ${r.question}${r.hit ? `  (rank ${r.rank})` : ""}`);

const hits = rows.filter((r) => r.hit).length;
const hitPct = Math.round((hits / rows.length) * 1000) / 10;
const summary = {
  date: new Date().toISOString(),
  index: { ...kbStats(), fields: "text + lead(x2) + pageTitle(x1.5), prefix, fuzzy 0.2, OR" },
  questions: rows.length,
  hits,
  hitPct,
  rank1: rows.filter((r) => r.rank === 1).length,
  rank2: rows.filter((r) => r.rank === 2).length,
  rank3: rows.filter((r) => r.rank === 3).length,
  threshold: THRESHOLD,
  pass: hitPct >= THRESHOLD && missingIds.length === 0,
  acceptedIdsMissingFromKb: missingIds,
  misses: rows.filter((r) => !r.hit).map(({ id, question, accept, returned }) => ({ id, question, accept, returned })),
};
console.log(JSON.stringify(summary, null, 2));
process.exit(summary.pass ? 0 : 1);
