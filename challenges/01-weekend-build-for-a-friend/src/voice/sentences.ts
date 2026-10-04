// Sentence splitting for speaking streamed text one sentence at a time. Pure, no DOM.

// A sentence ends at . ! ? (or a newline) followed by whitespace. A digit-dot-digit (1.5) never ends one.
const END = /([.!?]+["')\]]*|\n+)(\s+|$)/g;

/** Splits complete text into sentences; the last piece may lack end punctuation. */
export function splitSentences(text: string): string[] {
  const { sentences, rest } = takeSentences(text, true);
  return rest ? [...sentences, rest] : sentences;
}

/**
 * Takes complete sentences off the front of `buffer`.
 * With `final = false` a trailing fragment (no terminator seen yet) stays in `rest`.
 * A terminator at the very end of the buffer is held back when not final, because "1." may become "1.5".
 */
export function takeSentences(buffer: string, final = false): { sentences: string[]; rest: string } {
  const sentences: string[] = [];
  let start = 0;
  END.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = END.exec(buffer))) {
    const end = m.index + m[1]!.length;
    const atBufferEnd = m.index + m[0].length >= buffer.length;
    if (atBufferEnd && !final && m[2] === "") break; // no whitespace after it yet: wait for more text
    const piece = buffer.slice(start, end).trim();
    if (piece) sentences.push(piece);
    start = m.index + m[0].length;
  }
  let rest = buffer.slice(start);
  if (final) {
    const tail = rest.trim();
    if (tail) sentences.push(tail);
    rest = "";
  }
  return { sentences, rest };
}

/** Incremental splitter for token streams. */
export class SentenceStream {
  private buf = "";
  push(delta: string): string[] {
    this.buf += delta;
    const { sentences, rest } = takeSentences(this.buf, false);
    this.buf = rest;
    return sentences;
  }
  flush(): string[] {
    const { sentences } = takeSentences(this.buf, true);
    this.buf = "";
    return sentences;
  }
  reset(): void {
    this.buf = "";
  }
}

/** Cuts text to at most `max` characters, at a sentence boundary when one exists past the halfway point. */
export function truncateAtSentence(text: string, max: number): string {
  if (text.length <= max) return text;
  const cut = text.slice(0, max);
  let last = -1;
  const re = /[.!?]["')\]]*(?=\s|$)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(cut))) last = m.index + m[0].length;
  if (last > max / 2) return cut.slice(0, last).trim();
  const sp = cut.lastIndexOf(" ");
  return (sp > max / 2 ? cut.slice(0, sp) : cut).trim();
}
