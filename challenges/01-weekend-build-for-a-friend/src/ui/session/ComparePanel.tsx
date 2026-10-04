// "What affected run N?" panel (T4c, plan 5.3 and 4.7). SessionScreen fetches GET /api/analysis/compare and passes the
// result in; this component only renders it. Wording rules (docs/CHALLENGE-MEMORY.md): never claim a cause, never name a
// winner when the gap is inside the noise floor, label everything the driver tapped as his feel.
import type { Run, RunComparison } from "../../shared/types";
import { CitationChip } from "../app/components";
import { directionWord } from "../race/logic";
import { formatLap } from "./logic";
import "../race/compare.css";
import "./session.css";

export type { RunComparison };

export interface ComparePanelProps {
  /** Every run in the open session (for the "compare against" picker). */
  runs: Run[];
  /** The earlier run being compared against; null when the session has no earlier run. */
  runA: Run | null;
  /** The run the driver asked about. */
  runB: Run;
  /** Server result of /api/analysis/compare; null while loading or on error. */
  comparison: RunComparison | null;
  loading: boolean;
  error: string | null;
  /** Param id -> label, for the setup differences. */
  paramLabel: (id: string) => string;
  onPickA: (runId: string) => void;
  onClose: () => void;
}

const show = (v: unknown): string => (v === null || v === undefined || v === "" ? "not set" : String(v));
const s2 = (n: number): string => n.toFixed(2);

/** The server's effect text reads "<change>: notes say <effect>". The change is already a heading, so keep the notes part. */
export function notesPart(effect: string): string {
  const i = effect.indexOf(": notes say ");
  return i >= 0 ? `Notes say ${effect.slice(i + ": notes say ".length)}` : effect;
}

function Cites({ ids }: { ids?: string[] }) {
  const unique = [...new Set(ids ?? [])];
  if (!unique.length) return null;
  return (
    <div class="cp-cites" aria-label="Sources in the notes">
      {unique.map((id) => (
        <CitationChip key={id} id={id} />
      ))}
    </div>
  );
}

function verdictHeading(status: RunComparison["lapStats"]["status"]): string {
  if (status === "within-noise") return "No clear difference";
  if (status === "above-noise") return "A gap above the noise floor: a hint, not proof";
  return "Not enough timed laps";
}

export function ComparePanel(props: ComparePanelProps) {
  const { runs, runA, runB, comparison: c } = props;
  const others = runs.filter((r) => r.id !== runB.id);
  const ls = c?.lapStats;
  return (
    <div class="pc-panel se-compare" role="region" aria-label={`What affected run ${runB.seq}`}>
      <div class="pc-row" style="justify-content:space-between">
        <h3 style="margin:0">
          What affected run {runB.seq}
          {runA ? ` vs run ${runA.seq}` : ""}
        </h3>
        <button type="button" class="pc-btn" onClick={props.onClose}>
          Close
        </button>
      </div>
      {others.length > 0 && (
        <label class="pc-field" style="margin-top:12px">
          <span class="pc-label">Compare against</span>
          <select value={runA?.id ?? ""} onChange={(e) => props.onPickA((e.target as HTMLSelectElement).value)}>
            {others.map((r) => (
              <option key={r.id} value={r.id}>
                Run {r.seq}
                {r.bestLapMs ? `, best ${formatLap(r.bestLapMs)}` : ""}
              </option>
            ))}
          </select>
        </label>
      )}
      {!runA && <p class="pc-muted">There is no earlier run in this session to compare with.</p>}
      {props.loading && <p class="pc-muted">Comparing...</p>}
      {props.error && (
        <p class="pc-err" role="alert">
          Comparison not available: {props.error}
        </p>
      )}

      {c && ls && (
        <div data-testid="comparison">
          <div class="cp-section">
            <h4>Setup differences</h4>
            {c.setupDiffs.length === 0 ? (
              <p class="pc-muted">No setup difference between these runs.</p>
            ) : (
              <ul class="cp-list">
                {c.setupDiffs.map((d) => (
                  <li key={d.param} class="cp-item" data-kind="setup">
                    <div class="cp-change">
                      {props.paramLabel(d.param)}: {show(d.from)} to {show(d.to)} <span class="pc-muted">({directionWord(d.direction)})</span>
                    </div>
                    {d.effect ? <div class="cp-effect">{notesPart(d.effect)}</div> : <div class="cp-effect pc-muted">No note about this change in the lever table.</div>}
                    <Cites ids={d.citations} />
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div class="cp-section">
            <h4>Conditions</h4>
            {c.conditionDiffs.length === 0 ? (
              <p class="pc-muted">No notable condition difference.</p>
            ) : (
              <ul class="cp-list">
                {c.conditionDiffs.map((d, i) => (
                  <li key={i} class="cp-item" data-kind="cond">
                    <div>{d.text}</div>
                    <Cites ids={d.citations} />
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div class="cp-section">
            <h4>Lap times</h4>
            <div class="cp-verdict" data-status={ls.status} data-testid="lap-verdict">
              <div class="cp-verdict-head">{verdictHeading(ls.status)}</div>
              <p>{ls.text}</p>
              {ls.status !== "insufficient-data" && typeof ls.delta === "number" && (
                <>
                  <div class="cp-nums">
                    {typeof ls.meanA === "number" && (
                      <div class="cp-num">
                        <b>{s2(ls.meanA)} s</b>
                        <span>average lap, run A</span>
                      </div>
                    )}
                    {typeof ls.meanB === "number" && (
                      <div class="cp-num">
                        <b>{s2(ls.meanB)} s</b>
                        <span>average lap, run B</span>
                      </div>
                    )}
                    {typeof ls.diffS === "number" && (
                      <div class="cp-num">
                        <b>{`${ls.diffS > 0 ? "+" : ls.diffS < 0 ? "-" : ""}${s2(Math.abs(ls.diffS))} s`}</b>
                        <span>gap (run B minus run A)</span>
                      </div>
                    )}
                    <div class="cp-num">
                      <b>about {s2(ls.delta)} s</b>
                      <span>noise floor</span>
                    </div>
                  </div>
                  <p class="pc-small pc-muted">
                    In plain words: the noise floor is the smallest gap these laps can reliably show. A gap smaller than that looks the same as lap-to-lap wobble.
                  </p>
                </>
              )}
              <Cites ids={ls.citations} />
            </div>
          </div>

          {c.confounded && c.confoundText && (
            <div class="cp-flag" role="note" data-testid="confound">
              <p>{c.confoundText}</p>
              <Cites ids={c.confoundCitations} />
            </div>
          )}

          <details class="cp-how">
            <summary>? How is this computed</summary>
            <p>Setup differences: every setting that has a different value in the two runs. The note beside each one is the lever table's description of what that change usually does, with the notes it comes from.</p>
            <p>Conditions: track temperature 5 C or more apart, a different grip rating, surface or time of day, a tyre set with 3 or more extra runs on it, and the fact that a later run in the same session often has more grip.</p>
            <p>
              Lap times need 3 or more laps in each run. The noise floor is 2.8 x the pooled spread of the laps x the square root of (2 / number of laps in the shorter run). If the gap between the averages is smaller than the floor, the answer is "no clear difference" and no run is named as better.
              Laps within one run are not independent, so even a gap above the floor is a hint.
            </p>
            <p>This panel only lists what differed. It does not show what made any difference, and the notes recommend changing one thing at a time, back to back, to find out.</p>
            <Cites ids={["minimum-detectable-lap-time-difference#definition", "minimum-detectable-lap-time-difference#a-paired-back-to-back-testing-design-same"]} />
          </details>
          <p class="cp-foot">Your rating and feel taps are your own judgement, not lap-time proof.</p>
        </div>
      )}
    </div>
  );
}
