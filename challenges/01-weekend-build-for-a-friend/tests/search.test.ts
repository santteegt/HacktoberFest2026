import { describe, expect, it } from "vitest";
import { expandQuery, queryTerms, search, STOPWORDS, usesPrefix } from "../server/kb/search";

const ids = (q: string, n = 3) => search(q, n).map((c) => c.id);

describe("kb search: stopwords", () => {
  it("drops function words from a query and keeps the topic words", () => {
    expect(queryTerms("what does droop do")).toEqual(["droop"]);
    expect(queryTerms("How do I set the steering throw?")).toEqual(["set", "steering", "throw"]);
  });

  it("keeps domain words that look like function words", () => {
    // up, out, rear, front, more, left, right matter in this domain ("up-stops", "rear grip", "left/right").
    for (const w of ["up", "out", "rear", "front", "more", "left", "right"]) expect(STOPWORDS.has(w)).toBe(false);
    expect(queryTerms("more rear grip on exit")).toEqual(["more", "rear", "grip", "exit"]);
  });

  it("an all-stopword query returns nothing instead of matching everything", () => {
    expect(search("what is it to do")).toEqual([]);
    expect(search("   ")).toEqual([]);
  });

  it("answers 'what does droop do' with a droop chunk in the top 3", () => {
    const top = ids("what does droop do");
    expect(top.some((id) => id.includes("droop"))).toBe(true);
  });
});

describe("kb search: prefix rule", () => {
  it("is applied only to terms longer than 3 characters", () => {
    expect(usesPrefix("do")).toBe(false);
    expect(usesPrefix("arb")).toBe(false);
    expect(usesPrefix("epa")).toBe(false);
    expect(usesPrefix("droop")).toBe(true);
    expect(usesPrefix("ackermann")).toBe(true);
  });

  it("a 3-letter fragment does not prefix-match a long word, a 4-letter one does", () => {
    const droop = "touring-car-setup-procedure#droop-baselines";
    expect(ids("dro", 10)).not.toContain(droop);
    expect(ids("droo", 10)).toContain(droop);
  });
});

describe("kb search: domain vocabulary", () => {
  it("expands 'final drive ratio' to the notes' words (FDR, gearing)", () => {
    expect(expandQuery("final drive ratio formula")).toContain("fdr gearing");
    expect(ids("final drive ratio formula")).toContain("touring-car-drivetrain-tuning#gearing");
  });

  it("treats grip as traction and British spellings as the notes' spelling", () => {
    expect(expandQuery("more rear grip on exit")).toContain("traction");
    expect(queryTerms("tyres centre")).toEqual(["tires", "center"]);
    expect(ids("how often rotate tyres")).toContain("touring-car-traction-and-tire-management#tire-rotation-and-cycling");
  });

  it("returns real chunks only, with the limit respected", () => {
    const r = search("shock oil cst range", 2);
    expect(r.length).toBeLessThanOrEqual(2);
    expect(r[0]?.id).toBe("touring-car-suspension-tuning#shock-oil-viscosity");
  });
});
