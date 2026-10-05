// Keyword classifier (fallback and eval baseline) and canned refusals (T2; plan 4.3).
import type { Classification, Refusal, SymptomDef } from "../../src/shared/types";

// ---------- keywordClassify ----------

/** Below this score no symptom is returned and the caller falls back to the chips. */
export const KEYWORD_THRESHOLD = 0.5;

const STOPWORDS = new Set([
  "a", "an", "the", "i", "it", "its", "my", "me", "to", "of", "on", "in", "at", "is", "are", "was", "when",
  "and", "or", "but", "so", "that", "this", "with", "for", "out", "up", "car", "feels", "feel", "like", "gets",
  "get", "goes", "go", "keeps", "wont", "doesnt", "does", "do", "very", "really", "too", "just", "then",
]);

const normalize = (s: string) =>
  s
    .toLowerCase()
    .replace(/[‘’']/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();

/** Crude stemmer: enough to match "washes"/"wash", "bumps"/"bumpy", "sliding"/"slides". */
function stem(w: string): string {
  return w
    .replace(/(ing|ed|es|ies|y|s)$/, "")
    .replace(/(.)\1$/, "$1");
}

const contentTokens = (s: string) =>
  normalize(s)
    .split(" ")
    .filter((w) => w && !STOPWORDS.has(w))
    .map(stem)
    .filter((w) => w.length > 1);

interface Scored {
  symptom: SymptomDef;
  score: number;
}

function scoreSymptom(utt: string, uttTokens: Set<string>, s: SymptomDef): number {
  let best = 0;
  const padded = ` ${utt} `;
  for (const phrase of [...s.synonyms, s.label]) {
    const p = normalize(phrase);
    if (!p) continue;
    // 1. whole-phrase substring on word boundaries: strongest evidence; longer phrases are more specific
    if (padded.includes(` ${p} `)) {
      const words = p.split(" ").length;
      best = Math.max(best, Math.min(0.95, 0.75 + 0.05 * words));
      continue;
    }
    // 2. token overlap with the phrase's content words
    const toks = [...new Set(contentTokens(phrase))];
    if (!toks.length) continue;
    const hit = toks.filter((t) => uttTokens.has(t)).length;
    if (!hit) continue;
    const need = toks.length === 1 ? 1 : 2;
    if (hit < need) continue;
    best = Math.max(best, 0.8 * (hit / toks.length));
  }
  return best;
}

/** Synonym substring + token overlap; null below the threshold. */
export function keywordClassify(utterance: string, symptoms: SymptomDef[]): Classification | null {
  const utt = normalize(utterance);
  if (!utt) return null;
  const uttTokens = new Set(contentTokens(utterance));
  const scored: Scored[] = symptoms
    .filter((s) => s.id !== "out-of-scope" && s.synonyms.length > 0)
    .map((symptom) => ({ symptom, score: scoreSymptom(utt, uttTokens, symptom) }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score);
  const [top, second] = scored;
  if (!top || top.score < KEYWORD_THRESHOLD) return null;
  // A near tie between two symptoms is not a confident match: say so through a lower confidence.
  const margin = second ? top.score - second.score : top.score;
  const confidence = Math.max(0.3, Math.min(0.9, top.score - (margin < 0.1 ? 0.15 : 0)));
  return {
    symptomId: top.symptom.id,
    altId: second && second.score >= KEYWORD_THRESHOLD * 0.6 ? second.symptom.id : "none",
    phase: top.symptom.phase,
    confidence: Number(confidence.toFixed(2)),
    source: "keyword",
  };
}

// ---------- refusalFor ----------

const TYRE_GAP_CITATION = "touring-car-traction-and-tire-management#a-real-gap-not-an-extraction-failure";

export const REFUSAL_MESSAGES = {
  tyreCompoundGap:
    "I can't help with tyre compounds, shore hardness or inserts: my notes have no shore numbers and no foam or insert brands, and I won't guess. Ask a driver who runs your track. I can still help with the setup around the tyres.",
  electronics:
    "ESC, motor timing and boost settings are not in my notes, so I won't suggest values for them. Check the ESC maker's guide or ask your club. I can help with the chassis side of the problem.",
  nitro:
    "This app is for 1/10 electric touring cars. Nitro engines, glow plugs and needle settings are outside my notes.",
  battery:
    "Battery chargers and LiPo charging are a safety topic, and not in my notes. Follow the manufacturer's charging instructions. I can help with how the car drives.",
  otherCar:
    "I only know 1/10 on-road touring cars like the Yokomo BD12. Buggies, trucks, crawlers and drift cars set up differently, so I won't guess.",
} as const;

interface RefusalRule {
  reason: Refusal["reason"];
  message: string;
  citations: string[];
  test: RegExp;
}

// Order matters: first match wins. Patterns are word-bounded so "bumpy" or "motor gets hot" do not trip them
// ("motor gets hot" is a fade-late-run synonym and must reach the classifier).
const RULES: RefusalRule[] = [
  {
    reason: "tyre-compound-gap",
    message: REFUSAL_MESSAGES.tyreCompoundGap,
    citations: [TYRE_GAP_CITATION],
    test: /\bshore\b|\bcompounds?\b|\binserts?\b|\bfoams?\b|\bsorex\b|\b(which|what|best|recommend\w*)\b[^.?!]*\b(tyres?|tires?|rubbers?)\b/i,
  },
  {
    reason: "electronics",
    message: REFUSAL_MESSAGES.electronics,
    citations: [],
    test: /\besc\b|\bboost\b|\bturbo\b|\btiming advance\b|\bmotor timing\b|\bbrushless\b|\bsensored\b|\bkv\b|\b\d+(\.\d+)?\s?t\s+motor\b|\b(which|what|best)\b[^.?!]*\bmotors?\b|\bmotor (settings?|setup|tuning|profile)\b/i,
  },
  {
    reason: "other-car-type",
    message: REFUSAL_MESSAGES.nitro,
    citations: [],
    test: /\bnitro\b|\bglow\b|\bengines?\b|\bneedles?\b|\btwo[- ]?stroke\b/i,
  },
  {
    reason: "electronics",
    message: REFUSAL_MESSAGES.battery,
    citations: [],
    test: /\blipo\b|\bli[- ]po\b|\blithium\b|\bcharg(e|er|ers|ing)\b|\bdischarg\w*\b|\bnimh\b|\bmah\b/i,
  },
  {
    reason: "other-car-type",
    message: REFUSAL_MESSAGES.otherCar,
    citations: [],
    test: /\bbugg(y|ies)\b|\btruggy\b|\boff[- ]?road\b|\bcrawl(er|ers|ing)\b|\bmonster truck\b|\bshort course\b|\bdrift (car|setup|chassis|tuning)\b|\bdrifting\b|\b1\/8\b/i,
  },
];

/** Keyword refusals: tyre compound gap, ESC/motor, nitro, LiPo, off-road/other car types. */
export function refusalFor(utterance: string): Refusal | null {
  for (const rule of RULES) {
    if (rule.test.test(utterance)) {
      return { reason: rule.reason, message: rule.message, citations: [...rule.citations] };
    }
  }
  return null;
}

// ---------- offTopic ----------

/**
 * Words that mark a sentence as being about how an RC car drives or is set up. A sentence with none of them is
 * refused before any model call. Added on 2026-10-05 after the friend's laptop (gemma4:e2b-it-qat) answered
 * "hello" or "what time is it" with a handling symptom: the small model falls back to a symptom id on anything.
 * Deliberately generous (a false refusal costs one chip tap; a wrong suggestion costs a lap), and deliberately
 * without very common words such as "run", "time" or "good".
 */
const DOMAIN_WORDS =
  /\b(under|over)steer\w*|\bpush(es|ed|ing)?\b|\bplow\w*|\bwash(es|ed|ing)?\b|\bloose\b|\btail\b|\brear\b|\bfront\b|\bback\b|\bsteer\w*|\bturn\w*|\bcorner\w*|\bhairpin\w*|\bsweeper\w*|\bchicane\w*|\bapex\b|\bentry\b|\bexit\w*|\bbrak\w+|\bbreak(s|ing)?\b|\bthrottle\b|\bpower\b|\bgas\b|\baccelerat\w*|\bgrip\w*|\btraction\b|\bslid\w*|\bslip\w*|\bice\b|\bicy\b|\bdust\w*|\bbump\w*|\bbounc\w*|\bhop(s|ping)?\b|\bskip\w*|\btwitch\w*|\bdart\w*|\bnervous\b|\bedgy\b|\bfad(e|es|ed|ing)\b|\blaps?\b|\bstraight\b|\bwide\b|\bspin\w*|\bsnap\w*|\bfishtail\w*|\bflip\w*|\broll\w*|\btip(s|ped|ping)?\b|\bdig(s|ging)?\b|\blift\w*|\bwheels?\b|\btyres?\b|\btires?\b|\btrack\b|\bcar\b|\bchassis\b|\bset-?up\b|\bcamber\b|\btoe\b|\bcaster\b|\bdroop\b|\bride height\b|\bshocks?\b|\bdamper\w*|\bsprings?\b|\bdiff\w*|\bsway\b|\barb\b|\broll bar\b|\bweight\w*|\bbalance\w*|\bhandl\w*|\bone side\b|\bleft\b|\bright\b|\bbite\b|\bsettle\w*|\bstable\b|\bunstable\b|\bsensitive\b|\bsoft\b|\bstiff\b|\bdeviat\w*|\bpulls?\b|\bpulling\b|\blazy\b|\bsluggish\b|\bminutes?\b/i;

/** True when the sentence has no word about driving or setting up a car (see DOMAIN_WORDS). */
export function offTopic(utterance: string): boolean {
  return !DOMAIN_WORDS.test(utterance);
}
