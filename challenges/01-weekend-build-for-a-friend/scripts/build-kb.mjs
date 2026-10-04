// Compiles kb/source + kb/additions (OKF markdown) into data/generated/kb.json:
// one chunk per Definition and per top-level Key Points bullet, with stable readable ids.
// Also checks that every citation in data/levers.json resolves to a chunk.
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
      chunks.push({ id, page: slug, pageTitle: fm.title, section, lead, text: stripLinks(text).trim() });
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

let missing = 0;
if (existsSync("data/levers.json")) {
  for (const lever of JSON.parse(readFileSync("data/levers.json", "utf8"))) {
    for (const c of lever.citations ?? []) if (!seen.has(c)) { console.error(`lever ${lever.id}: unknown citation ${c}`); missing++; }
  }
}
const words = chunks.reduce((n, c) => n + c.text.split(/\s+/).length, 0);
console.log(`kb: ${pages.length} pages, ${chunks.length} chunks, ${words} words`);
if (missing) process.exit(1);
