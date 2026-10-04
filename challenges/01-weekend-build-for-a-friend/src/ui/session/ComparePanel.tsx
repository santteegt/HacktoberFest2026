// "What affected run N?" panel. T4b placeholder: renders the RunComparison type (src/shared) as plain lists.
// HANDED OVER to T4c, who fills in the final layout. The props type below is the contract with SessionScreen:
// SessionScreen fetches GET /api/analysis/compare and passes the result in; this component only renders.
import type { Run, RunComparison } from "../../shared/types";
import { formatLap } from "./logic";
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

export function ComparePanel(props: ComparePanelProps) {
  const { runs, runA, runB, comparison: c } = props;
  const others = runs.filter((r) => r.id !== runB.id);
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
      {c && (
        <div>
          <h3>Setup</h3>
          {c.setupDiffs.length === 0 ? (
            <p class="pc-muted">No setup difference between these runs.</p>
          ) : (
            <ul>
              {c.setupDiffs.map((d) => (
                <li key={d.param}>
                  {props.paramLabel(d.param)}: {String(d.from ?? "not set")} to {String(d.to ?? "not set")}
                  {d.effect ? ` (notes: ${d.effect})` : ""}
                </li>
              ))}
            </ul>
          )}
          <h3>Conditions</h3>
          {c.conditionDiffs.length === 0 ? (
            <p class="pc-muted">No notable condition difference.</p>
          ) : (
            <ul>
              {c.conditionDiffs.map((d, i) => (
                <li key={i}>{d.text}</li>
              ))}
            </ul>
          )}
          <h3>Lap times</h3>
          <p>{c.lapStats.text}</p>
          {c.confounded && c.confoundText && <p class="pc-flag">{c.confoundText}</p>}
        </div>
      )}
      <p class="pc-small pc-muted">Placeholder layout: T4c replaces this component's body.</p>
    </div>
  );
}
