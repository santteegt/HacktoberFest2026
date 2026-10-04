// "Compare with a saved setup" (T4b): pick a saved setup, see every param that differs from the current setup.
// The picked entry's setup row comes from GET /api/setups/:id (T7), not the whole export.
import { useEffect, useState } from "preact/hooks";
import { request } from "../../api/client";
import type { ParamDef, SavedSetup, Setup, SetupValues } from "../../shared/types";
import { conditionsSummary } from "./SaveSetupDialog";
import { deltaText, diffValues, formatValue } from "./logic";
import { errorMessage } from "./widgets";

export function CompareSaved(props: { params: ParamDef[]; current: SetupValues; refreshKey?: number }) {
  const [saved, setSaved] = useState<SavedSetup[]>([]);
  const [setups, setSetups] = useState<Map<string, Setup | null>>(new Map());
  const [picked, setPicked] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let live = true;
    setLoading(true);
    (async () => {
      try {
        const list = await request("GET /api/saved");
        if (!live) return;
        setSaved(list);
        setSetups(new Map());
        setErr(null);
      } catch (e) {
        if (live) setErr(errorMessage(e));
      } finally {
        if (live) setLoading(false);
      }
    })();
    return () => {
      live = false;
    };
  }, [props.refreshKey]);

  const sel = saved.find((s) => s.id === picked);
  const setupId = sel?.setupId;
  useEffect(() => {
    if (!setupId || setups.has(setupId)) return;
    let live = true;
    request("GET /api/setups/:id", undefined, { params: { id: setupId } })
      .then((su) => live && setSetups((m) => new Map(m).set(setupId, su)))
      .catch(() => live && setSetups((m) => new Map(m).set(setupId, null)));
    return () => {
      live = false;
    };
  }, [setupId, setups]);
  const fetched = setupId ? setups.get(setupId) : undefined;
  const selSetup = fetched ?? undefined;
  const diffs = selSetup ? diffValues(props.current, selSetup.values, props.params) : [];
  const label = (id: string) => props.params.find((p) => p.id === id);

  return (
    <div class="pc-panel">
      <h3>Compare with a saved setup</h3>
      {err && <p class="pc-err" role="alert">Could not load saved setups: {err}</p>}
      {!err && !loading && saved.length === 0 && (
        <p class="pc-muted">No saved setups yet. Save one from a session that went well.</p>
      )}
      {saved.length > 0 && (
        <label class="pc-field">
          <span class="pc-label">Saved setup</span>
          <select value={picked} onChange={(e) => setPicked((e.target as HTMLSelectElement).value)}>
            <option value="">Choose one...</option>
            {saved.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label} ({s.conditions.trackName || "no track"})
              </option>
            ))}
          </select>
        </label>
      )}
      {sel && (
        <>
          <p class="pc-small pc-muted">{conditionsSummary(sel.conditions)}</p>
          {sel.verdict && <p class="pc-small">Verdict: {sel.verdict}</p>}
          {fetched === undefined && <p class="pc-muted">Loading…</p>}
          {fetched === null && <p class="pc-err">The setup row for this saved entry was not found.</p>}
          {selSetup && diffs.length === 0 && <p class="pc-ok">Identical to your current setup.</p>}
          {selSetup && diffs.length > 0 && (
            <table class="pc-table">
              <thead>
                <tr>
                  <th>Setting</th>
                  <th>Current</th>
                  <th>Saved</th>
                  <th>To get there</th>
                </tr>
              </thead>
              <tbody>
                {diffs.map((d) => {
                  const p = label(d.param);
                  return (
                    <tr key={d.param}>
                      <td>{p?.label ?? d.param}</td>
                      <td>{formatValue(d.from, p?.unit)}</td>
                      <td>{formatValue(d.to, p?.unit)}</td>
                      <td>{deltaText(d.from, d.to)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
