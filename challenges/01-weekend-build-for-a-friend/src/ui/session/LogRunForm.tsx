// LOG RUN form (T4b, plan 4.5): rating 1-5, feel chips, best lap, pasted lap times, tyre-runs counter, note.
// The setup is implicit: the session's current setup. When the tyre-runs counter changed, that value is written
// to a new setup row first (source "manual", param tyreRunsOnSet) so the run's setup carries the tyre wear.
import { useEffect, useState } from "preact/hooks";
import { request } from "../../api/client";
import type { Rating, Run, Session, Setup, SymptomDef } from "../../shared/types";
import { ChipMulti, errorMessage } from "../setup/widgets";
import { bestOf, formatLap, nextTyreRuns, parseLapTimes, parseOneLap } from "./logic";

export const TYRE_PARAM = "tyreRunsOnSet";

export function LogRunForm(props: {
  session: Session;
  setup: Setup | null;
  symptoms: SymptomDef[];
  /** Runs so far, for the next run number. */
  runCount: number;
  /** Called with the saved run and the new current setup (when the tyre counter was written). */
  onLogged: (run: Run, newSetup: Setup | null) => void;
  onCancel: () => void;
}) {
  const current = props.setup?.values[TYRE_PARAM];
  const suggested = nextTyreRuns(current);
  const [rating, setRating] = useState<Rating | undefined>();
  const [feel, setFeel] = useState<string[]>([]);
  const [bestText, setBestText] = useState("");
  const [lapsText, setLapsText] = useState("");
  const [tyre, setTyre] = useState(suggested);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // The counter follows the setup row (a new row appears after each logged run or commit).
  useEffect(() => setTyre(suggested), [props.setup?.id, suggested]);

  const parsed = parseLapTimes(lapsText);
  const feelOptions = props.symptoms
    .filter((s) => s.id !== "out-of-scope")
    .map((s) => ({ value: s.id, label: s.label, title: s.synonyms.slice(0, 4).join(", ") }));

  async function submit(e: Event) {
    e.preventDefault();
    if (parsed.bad.length) {
      setErr(`Not a lap time: ${parsed.bad.join(", ")}. Use seconds like 14.9, separated by spaces or commas.`);
      return;
    }
    let bestMs: number | undefined;
    if (bestText.trim()) {
      const b = parseOneLap(bestText.trim());
      if (b === null) {
        setErr("Best lap must be seconds like 14.82.");
        return;
      }
      bestMs = b;
    } else {
      bestMs = bestOf(parsed.laps);
    }
    setBusy(true);
    setErr(null);
    try {
      let setup: Setup | null = null;
      if (tyre !== (typeof current === "number" ? current : null)) {
        const res = await request(
          "POST /api/sessions/:id/setup",
          { values: { [TYRE_PARAM]: tyre }, source: "manual" },
          { params: { id: props.session.id } },
        );
        setup = res.setup;
      }
      const run = await request(
        "POST /api/sessions/:id/runs",
        {
          sessionId: props.session.id,
          feel,
          ...(rating ? { rating } : {}),
          ...(bestMs !== undefined ? { bestLapMs: bestMs } : {}),
          ...(parsed.laps.length ? { lapTimesMs: parsed.laps } : {}),
          ...(note.trim() ? { notes: note.trim() } : {}),
        },
        { params: { id: props.session.id } },
      );
      props.onLogged(run, setup);
    } catch (e2) {
      setErr(errorMessage(e2));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form class="pc-panel se-logrun" onSubmit={submit} aria-label="Log run">
      <h3>Log run {props.runCount + 1}</h3>
      <div class="pc-field">
        <span class="pc-label">How did it go?</span>
        <div class="se-rating" role="radiogroup" aria-label="Rating">
          {([1, 2, 3, 4, 5] as Rating[]).map((n) => (
            <button
              key={n}
              type="button"
              role="radio"
              class="pc-btn big"
              aria-checked={rating === n}
              aria-label={`Rating ${n}`}
              onClick={() => setRating(rating === n ? undefined : n)}
            >
              {n}
            </button>
          ))}
        </div>
        <span class="pc-small pc-muted">1 = bad, 5 = great</span>
      </div>
      <div class="pc-field">
        <span class="pc-label">What did the car do? (tap any)</span>
        <ChipMulti label="Feel" options={feelOptions} value={feel} onChange={setFeel} />
      </div>
      <label class="pc-field" style="max-width:260px">
        <span class="pc-label">Best lap, seconds (optional)</span>
        <input type="text" inputMode="decimal" placeholder="14.82" value={bestText} onInput={(e) => setBestText((e.target as HTMLInputElement).value)} />
      </label>
      <label class="pc-field">
        <span class="pc-label">Lap times, seconds (optional, paste them: spaces or commas)</span>
        <textarea placeholder="14.9 15.1, 14.8" value={lapsText} onInput={(e) => setLapsText((e.target as HTMLTextAreaElement).value)} />
        {lapsText.trim() && (
          <span class={parsed.bad.length ? "pc-err" : "pc-small pc-muted"}>
            {parsed.bad.length
              ? `Not a lap time: ${parsed.bad.join(", ")}`
              : `${parsed.laps.length} lap${parsed.laps.length === 1 ? "" : "s"}, best ${formatLap(bestOf(parsed.laps))} s`}
          </span>
        )}
      </label>
      <div class="pc-field">
        <span class="pc-label">Runs on this tyre set (counting this one)</span>
        <div class="pc-row">
          <button type="button" class="pc-btn" aria-label="Fewer tyre runs" onClick={() => setTyre(Math.max(0, tyre - 1))}>
            -
          </button>
          <strong class="se-tyre" aria-live="polite">{tyre}</strong>
          <button type="button" class="pc-btn" aria-label="More tyre runs" onClick={() => setTyre(tyre + 1)}>
            +
          </button>
          <button type="button" class="pc-btn" onClick={() => setTyre(1)}>
            New tyre set
          </button>
        </div>
      </div>
      <label class="pc-field">
        <span class="pc-label">Note (optional)</span>
        <input type="text" value={note} onInput={(e) => setNote((e.target as HTMLInputElement).value)} />
      </label>
      {err && (
        <p class="pc-err" role="alert">
          {err}
        </p>
      )}
      <div class="pc-row">
        <button type="submit" class="pc-btn primary" disabled={busy}>
          {busy ? "Saving..." : "Save run"}
        </button>
        <button type="button" class="pc-btn" onClick={props.onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
