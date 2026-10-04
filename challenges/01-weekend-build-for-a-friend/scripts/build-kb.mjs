// Compiles kb/source + kb/additions (OKF markdown) into data/generated/kb.json:
// one chunk per Definition and per top-level Key Points bullet, with stable readable ids.
// Also cross-checks data/*.json: citations resolve to chunks, lever params and symptom prechecks to known ids.
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, readdirSync, existsSync, writeFileSync } from "node:fs";

const DIRS = ["kb/source", "kb/additions"];
const slugify = (s) =>
  s.toLowerCase().replace(/[`*_]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48);

function parse(md) {
  const m = md.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!m) throw new Error("missing frontmatter");
  const fm = {};
  for (const line of m[1].split("\n")) {
    const kv = line.match(/^([a-zA-Z_]+):\s*(.*)$/);
    if (kv) fm[kv[1]] = kv[2].replace(/^"(.*)"$/, "$1");
  }
  return { fm, body: m[2] };
}
function sections(body) {
  const out = {};
  let cur = null;
  for (const line of body.split("\n")) {
    const h = line.match(/^## (.+)$/);
    if (h) { cur = h[1].trim(); out[cur] = []; } else if (cur) out[cur].push(line);
  }
  return out;
}
function bullets(lines) {
  const items = [];
  for (const line of lines) {
    if (/^- /.test(line)) items.push(line.slice(2));
    else if (items.length && line.trim()) items[items.length - 1] += " " + line.trim();
  }
  return items;
}
const stripLinks = (s) => s.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");

const pages = [], chunks = [], seen = new Set();
const hash = createHash("sha256");
for (const dir of DIRS) {
  if (!existsSync(dir)) continue;
  for (const name of readdirSync(dir).filter((n) => n.endsWith(".md") && n.toLowerCase() !== "readme.md").sort()) {
    const md = readFileSync(`${dir}/${name}`, "utf8");
    hash.update(md);
    const { fm, body } = parse(md);
    const slug = name.replace(/\.md$/, "");
    const sec = sections(body);
    const related = [...(sec["Related Concepts"] ?? []).join("\n").matchAll(/\]\(([a-z0-9\-]+)\.md\)/g)].map((x) => x[1]);
    pages.push({ slug, origin: dir.split("/")[1], title: fm.title, description: fm.description, tags: (fm.tags ?? "").replace(/[\[\]]/g, "").split(",").map((t) => t.trim()).filter(Boolean), related });
    const add = (section, lead, text) => {
      let id = `${slug}#${slugify(lead)}`, n = 2;
      while (seen.has(id)) id = `${slug}#${slugify(lead)}-${n++}`;
      seen.add(id);
      // origin: "snapshot" = frozen pre-window notes (kb/source), "additions" = written in the window (kb/additions).
      chunks.push({ id, page: slug, pageTitle: fm.title, origin: dir === "kb/additions" ? "additions" : "snapshot", section, lead, text: stripLinks(text).trim() });
    };
    const def = (sec["Definition"] ?? []).join(" ").trim();
    if (def) add("Definition", "definition", def);
    for (const b of bullets(sec["Key Points"] ?? [])) {
      const bold = b.match(/^\*\*(.+?)\*\*/);
      add("Key Points", bold ? bold[1] : b.split(/\s+/).slice(0, 6).join(" "), b);
    }
  }
}
mkdirSync("data/generated", { recursive: true });
writeFileSync("data/generated/kb.json", JSON.stringify({ contentHash: hash.digest("hex"), pages, chunks }, null, 1));

// Cross-checks the domain data: every citation must be a known chunk id, every lever param a known
// param id, every precheck id used by a symptom a known precheck, every lever symptom a known symptom.
const readJson = (f) => (existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : null);
const params = readJson("data/params.bd12.json")?.params ?? [];
const symptoms = readJson("data/symptoms.json") ?? [];
const prechecks = readJson("data/prechecks.json") ?? [];
const levers = readJson("data/levers.json") ?? [];
const paramIds = new Set(params.map((p) => p.id));
const symptomIds = new Set(symptoms.map((s) => s.id));
const precheckIds = new Set(prechecks.map((p) => p.id));
let missing = 0;
const bad = (msg) => { console.error(msg); missing++; };
for (const p of params) for (const c of p.src ?? []) if (!seen.has(c)) bad(`param ${p.id}: unknown citation ${c}`);
for (const p of prechecks) for (const c of p.citations ?? []) if (!seen.has(c)) bad(`precheck ${p.id}: unknown citation ${c}`);
for (const s of symptoms) for (const id of s.prechecks ?? []) if (!precheckIds.has(id)) bad(`symptom ${s.id}: unknown precheck ${id}`);
for (const l of levers) {
  for (const c of l.citations ?? []) if (!seen.has(c)) bad(`lever ${l.id}: unknown citation ${c}`);
  if (l.param !== undefined && !paramIds.has(l.param)) bad(`lever ${l.id}: unknown param ${l.param}`);
  if (!symptomIds.has(l.symptomId)) bad(`lever ${l.id}: unknown symptom ${l.symptomId}`);
}
console.log(`data: ${params.length} params, ${symptoms.length} symptoms, ${prechecks.length} prechecks, ${levers.length} levers (${levers.filter((l) => l.status === "reviewed").length} reviewed); ${missing} unknown citations/params/prechecks`);
const words = chunks.reduce((n, c) => n + c.text.split(/\s+/).length, 0);
console.log(`kb: ${pages.length} pages, ${chunks.length} chunks, ${words} words`);
if (missing) process.exit(1);
