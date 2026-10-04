// Mounted once in App: shows the citation drawer for the chunk id set by openCitation().
import { useEffect, useState } from "preact/hooks";
import { kbChunk } from "../../api/client";
import type { KbChunk } from "../../shared/types";
import { Banner, Drawer } from "./components";
import { closeCitation, openId } from "./drawer";

const cache = new Map<string, KbChunk>();

/** The server tags every chunk with its origin (kb/source snapshot vs kb/additions written in the window). */
function originLabel(c: KbChunk): string {
  return c.origin === "additions"
    ? "Added in the challenge window (NotebookLM extraction)"
    : "From the author's pre-window notes";
}

export function DrawerHost() {
  const id = openId.value;
  const [chunk, setChunk] = useState<KbChunk | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    setErr(null);
    if (!id) return setChunk(null);
    const hit = cache.get(id);
    if (hit) return setChunk(hit);
    setChunk(null);
    let live = true;
    kbChunk(id)
      .then((c) => {
        cache.set(id, c);
        if (live) setChunk(c);
      })
      .catch((e: Error) => live && setErr(e.message));
    return () => {
      live = false;
    };
  }, [id]);
  return (
    <Drawer open={!!id} title={chunk?.pageTitle ?? "Note"} onClose={closeCitation}>
      {err && <Banner tone="danger">Could not load that note: {err}</Banner>}
      {!chunk && !err && <p class="muted">Loading…</p>}
      {chunk && (
        <>
          <span class="drawer-tag">{originLabel(chunk)}</span>
          <div class="muted small">
            {chunk.section} · <code>{chunk.id}</code>
          </div>
          <p class="drawer-text">{chunk.text.replace(/\*\*/g, "")}</p>
        </>
      )}
    </Drawer>
  );
}
