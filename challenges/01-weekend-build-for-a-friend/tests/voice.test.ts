// Voice tests (T6): sentence splitter, `say` argument builder, /api/speak validation. No audio is produced here.
import { describe, expect, it } from "vitest";
import { Hono } from "hono";
import speak, { MAX_SPEAK_CHARS, buildSayArgs, parseSpeakBody } from "../server/routes/speak";
import { SentenceStream, splitSentences, takeSentences, truncateAtSentence } from "../src/voice/sentences";
import { PIT_PHRASES } from "../src/voice/phrases";

describe("splitSentences", () => {
  it("splits on . ! ? and keeps decimals together", () => {
    expect(splitSentences("Raise the front camber to 1.5 degrees. Then check toe! Ready?")).toEqual([
      "Raise the front camber to 1.5 degrees.",
      "Then check toe!",
      "Ready?",
    ]);
  });
  it("keeps a trailing fragment and handles newlines", () => {
    expect(splitSentences("One.\nTwo and a half")).toEqual(["One.", "Two and a half"]);
    expect(splitSentences("")).toEqual([]);
  });
});

describe("SentenceStream", () => {
  it("emits sentences as tokens arrive and holds a digit-dot until it is clear", () => {
    const s = new SentenceStream();
    const out: string[] = [];
    for (const tok of ["Set cam", "ber to 1.", "5 deg", "rees. Next", " step is toe.", " Done"]) out.push(...s.push(tok));
    expect(out).toEqual(["Set camber to 1.5 degrees.", "Next step is toe."]);
    expect(s.flush()).toEqual(["Done"]);
  });
  it("takeSentences non-final leaves the open fragment", () => {
    expect(takeSentences("A. B", false)).toEqual({ sentences: ["A."], rest: "B" });
  });
});

describe("truncateAtSentence", () => {
  it("cuts at a sentence boundary under the limit", () => {
    const t = "Aaaa bbbb. Cccc dddd. Eeee ffff gggg hhhh.";
    expect(truncateAtSentence(t, 25)).toBe("Aaaa bbbb. Cccc dddd.");
    expect(truncateAtSentence("short", 25)).toBe("short");
  });
});

describe("buildSayArgs / parseSpeakBody", () => {
  it("builds an args array; -- protects text that starts with a dash", () => {
    expect(buildSayArgs("hello")).toEqual(["--", "hello"]);
    expect(buildSayArgs("-v evil", "Samantha")).toEqual(["-v", "Samantha", "--", "-v evil"]);
  });
  it("accepts plain voices and rejects shell metacharacters", () => {
    expect(parseSpeakBody({ text: "x", voice: "Daniel" }).ok).toBe(true);
    expect(parseSpeakBody({ text: "x", voice: "Good News" }).ok).toBe(true);
    for (const v of ["Daniel; rm -rf ~", "$(id)", "a|b", "`x`", "-v", "a\nb", "Eddy (English)", "../x"]) {
      expect(parseSpeakBody({ text: "x", voice: v }).ok, v).toBe(false);
    }
  });
  it("rejects empty and non-string text, limits long text, supports cancel", () => {
    expect(parseSpeakBody({ text: "   " }).ok).toBe(false);
    expect(parseSpeakBody({ text: 5 }).ok).toBe(false);
    expect(parseSpeakBody(null).ok).toBe(false);
    const long = parseSpeakBody({ text: "word ".repeat(400) });
    expect(long.ok && !long.cancel && long.text.length <= MAX_SPEAK_CHARS && long.truncated).toBe(true);
    expect(parseSpeakBody({ cancel: true })).toEqual({ ok: true, cancel: true });
  });
});

describe("/api/speak validation over HTTP", () => {
  const app = new Hono().route("/", speak);
  const post = (body: unknown) =>
    app.request("/speak", { method: "POST", body: typeof body === "string" ? body : JSON.stringify(body) });
  it("returns 400 for a metacharacter voice, bad JSON and empty text, before spawning anything", async () => {
    expect((await post({ text: "hi", voice: "x; touch /tmp/pwned" })).status).toBe(400);
    expect((await post("not json")).status).toBe(400);
    expect((await post({ text: "" })).status).toBe(400);
  });
  it("cancel with nothing playing is ok", async () => {
    const res = await app.request("/speak", { method: "DELETE" });
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, cancelled: false });
  });
});

describe("phrases", () => {
  it("covers the pit vocabulary", () => {
    for (const w of ["droop", "Ackermann", "caster", "camber", "toe", "bump steer", "anti-roll bar", "understeer", "oversteer", "traction roll", "ride height", "diff oil"]) {
      expect(PIT_PHRASES).toContain(w);
    }
  });
});
