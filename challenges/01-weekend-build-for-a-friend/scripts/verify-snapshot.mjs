// Fails if any file in kb/source was changed since import (the snapshot is frozen:
// corrections belong in kb/additions, never in kb/source).
import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";

const manifest = JSON.parse(readFileSync("kb/snapshot-manifest.json", "utf8"));
let bad = 0;
for (const f of manifest.files) {
  const sum = createHash("sha256").update(readFileSync(`kb/${f.file}`)).digest("hex");
  if (sum !== f.sha256) {
    console.error(`CHANGED  kb/${f.file}`);
    bad++;
  }
}
const listed = new Set(manifest.files.map((f) => f.file.replace("source/", "")));
for (const name of readdirSync("kb/source")) {
  if (!listed.has(name)) {
    console.error(`UNLISTED kb/source/${name} (add it via a new import, or move it to kb/additions)`);
    bad++;
  }
}
if (bad) process.exit(1);
console.log(`snapshot ok: ${manifest.files.length} files unchanged`);
