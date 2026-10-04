// Offline knowledge: a frozen, credited snapshot of the author's touring-car notes
// (see kb/PROVENANCE.md) chunked to public/kb.json at build time.

export interface KbChunk {
  id: string; // stable id referenced by data/levers.json citations
  page: string; // source page slug in the snapshot
  heading: string;
  text: string;
}

export interface KbSearch {
  search(query: string, limit?: number): KbChunk[];
  get(id: string): KbChunk | undefined;
}
