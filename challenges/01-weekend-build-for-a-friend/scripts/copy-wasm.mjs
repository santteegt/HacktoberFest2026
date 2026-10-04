// Self-host the LiteRT-LM WASM runtime so nothing is fetched from a CDN at runtime
// (the package defaults to jsDelivr, which would break any offline claim).
import { cpSync, existsSync, mkdirSync } from "node:fs";

const from = "node_modules/@litert-lm/core/wasm";
const to = "public/litert-wasm";
if (!existsSync(from)) {
  console.error(`missing ${from}; run npm install first`);
  process.exit(1);
}
mkdirSync(to, { recursive: true });
cpSync(from, to, { recursive: true });
console.log(`copied ${from} -> ${to}`);
