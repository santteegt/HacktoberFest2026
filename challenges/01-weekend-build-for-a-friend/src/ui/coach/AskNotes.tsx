// "Ask the notes": keyword search over the knowledge base (GET /api/kb/search). No model call.
import { useState } from "preact/hooks";
import { kbSearch } from "../../api/client";
import type { KbChunk } from "../../shared/types";
import { Banner, Button, Card } from "../app/components";
import { openCitation } from "../app/drawer";

const snippet = (text: string) => (text.length > 260 ? `${text.slice(0, 259).trimEnd()}…` : text);

export function AskNotes() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<KbChunk[] | null>(null);
  const [asked, setAsked] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    const query = q.trim();
    if (!query) return;
    setLoading(true);
    setErr(null);
    try {
      setResults(await kbSearch(query, 3));
      setAsked(query);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="Ask the notes" class="ask">
      <div class="stack">
        <div class="row">
          <input
            class="field grow"
            value={q}
            placeholder="why does droop matter?"
            aria-label="Ask the notes"
            onInput={(e) => setQ((e.target as HTMLInputElement).value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void run();
              }
            }}
          />
          <Button disabled={loading || !q.trim()} onClick={() => void run()}>
            {loading ? "Searching…" : "Search"}
          </Button>
        </div>
        <p class="muted small">Searches the author's notes directly. No model is involved, so it works with Ollama off.</p>
        {err && <Banner tone="danger">{err}</Banner>}
        {results && results.length === 0 && <p class="muted">Nothing in my notes matches "{asked}".</p>}
        {results && results.length > 0 && (
          <div class="notes-grid">
            {results.map((c) => (
              <article class="note-card" key={c.id}>
                <div class="muted small">{c.pageTitle}</div>
                <b>{c.lead}</b>
                <p class="small">{snippet(c.text)}</p>
                <Button onClick={() => openCitation(c.id)}>Read the note</Button>
              </article>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
