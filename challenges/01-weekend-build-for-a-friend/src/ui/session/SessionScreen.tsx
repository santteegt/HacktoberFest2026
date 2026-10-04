// Session screen (T4b, plan 5.3): start-session form, edit conditions, LOG RUN, run list, change list with outcomes,
// "What affected run N?" (ComparePanel, filled in by T4c).
import { useEffect, useState } from "preact/hooks";
import { request } from "../../api/client";
import type { Change, Outcome, ParamDef, Run, Session } from "../../shared/types";
import { SaveSetupDialog, conditionsSummary } from "../setup/SaveSetupDialog";
import { diffValues, formatValue } from "../setup/logic";
import { stagedCount } from "../setup/staged";
import { errorMessage } from "../setup/widgets";
import "../setup/widgets.css";
import { currentSetup, meta, session, settings } from "../store";
import { bundle, bundleError, ensureBundle, openSession, refreshBundle, setupById } from "./bundle";
import { ComparePanel } from "./ComparePanel";
import { ConditionsForm } from "./ConditionsForm";
import { LogRunForm, TYRE_PARAM } from "./LogRunForm";
import { formatLap, timeOfDayLabel, today } from "./logic";
import type { RunComparison } from "./ComparePanel";
import "./session.css";

export function SessionScreen() {
  const s = session.value;
  const m = meta.value;
  const b = bundle.value;
  const [past, setPast] = useState<Session[]>([]);
  const [mode, setMode] = useState<"none" | "log" | "edit" | "new">("none");
  const [showSave, setShowSave] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [cmpB, setCmpB] = useState<string | null>(null);
  const [cmpA, setCmpA] = useState<string | null>(null);
  const [cmp, setCmp] = useState<RunComparison | null>(null);
  const [cmpLoading, setCmpLoading] = useState(false);
  const [cmpErr, setCmpErr] = useState<string | null>(null);

  useEffect(() => {
    void ensureBundle();
  }, [s?.id]);

  useEffect(() => {
    let live = true;
    request("GET /api/sessions")
      .then((l) => live && setPast(l))
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [s?.id]);

  // Fetch the run comparison whenever the pair changes.
  useEffect(() => {
    if (!cmpB || !cmpA) {
      setCmp(null);
      setCmpErr(null);
      return;
    }
    let live = true;
    setCmpLoading(true);
    setCmpErr(null);
    request("GET /api/analysis/compare", undefined, { query: { runA: cmpA, runB: cmpB } })
      .then((r) => live && setCmp(r))
      .catch((e) => {
        if (live) {
          setCmp(null);
          setCmpErr(errorMessage(e));
        }
      })
      .finally(() => live && setCmpLoading(false));
    return () => {
      live = false;
    };
  }, [cmpA, cmpB]);

  const params: ParamDef[] = m?.params ?? [];
  const label = (id: string) => params.find((p) => p.id === id)?.label ?? id;
  const car = settings.value?.car ?? m?.car ?? "yokomo-bd12";

  async function startSession(conditions: Session["conditions"]) {
    const created = await request("POST /api/sessions", { date: today(), car, conditions });
    await openSession(created.id);
    setMode("none");
    setCmpB(null);
    setNote("Session started.");
  }

  async function updateConditions(conditions: Session["conditions"]) {
    if (!s) return;
    const updated = await request("PATCH /api/sessions/:id", { conditions }, { params: { id: s.id } });
    session.value = updated;
    await refreshBundle();
    setMode("none");
  }

  async function setOutcome(c: Change, outcome: Outcome) {
    setErr(null);
    try {
      await request("PATCH /api/changes/:id", { outcome }, { params: { id: c.id } });
      await refreshBundle();
    } catch (e) {
      setErr(errorMessage(e));
    }
  }

  function openCompare(run: Run) {
    const runs = bundle.value?.runs ?? [];
    const idx = runs.findIndex((r) => r.id === run.id);
    setCmpB(run.id);
    setCmpA(idx > 0 ? runs[idx - 1].id : (runs.find((r) => r.id !== run.id)?.id ?? null));
  }

  // ----- no open session: start form + resume list -----
  if (!s) {
    const recent = [...past].sort((a, c) => c.createdAt - a.createdAt).slice(0, 5);
    return (
      <section class="screen pcx" aria-labelledby="session-title">
        <h2 id="session-title">Start a practice session</h2>
        <div class="pc-panel">
          <ConditionsForm submitLabel="Start session" past={past} onSubmit={startSession} />
        </div>
        {recent.length > 0 && (
          <div class="pc-panel">
            <h3>Or continue a recent session</h3>
            <div class="pc-chips">
              {recent.map((r) => (
                <button key={r.id} type="button" class="pc-btn" onClick={() => void openSession(r.id)}>
                  {r.conditions.trackName || "Session"}, {r.date}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    );
  }

  const runs = b?.runs ?? [];
  const runsDesc = [...runs].sort((x, y) => y.seq - x.seq);
  const changes = (b?.changes ?? []).filter((c) => c.param !== TYRE_PARAM).sort((x, y) => y.createdAt - x.createdAt);
  const runB = runs.find((r) => r.id === cmpB) ?? null;
  const runA = runs.find((r) => r.id === cmpA) ?? null;
  const latest = runs.length ? runs[runs.length - 1] : undefined;

  /** Setup differences between a run and the run before it (the tyre-run counter is bookkeeping, so it is left out). */
  function setupNote(run: Run): string {
    const idx = runs.findIndex((r) => r.id === run.id);
    if (idx <= 0) return "";
    const prev = setupById(runs[idx - 1].setupId);
    const cur = setupById(run.setupId);
    if (!prev || !cur) return "";
    const d = diffValues(prev.values, cur.values, params).filter((x) => x.param !== TYRE_PARAM);
    if (!d.length) return "";
    return d
      .slice(0, 3)
      .map((x) => {
        const p = params.find((q) => q.id === x.param);
        return `${label(x.param)} ${formatValue(x.from, p?.unit)} to ${formatValue(x.to, p?.unit)}`;
      })
      .join("; ") + (d.length > 3 ? `; +${d.length - 3} more` : "");
  }

  const feelLabel = (id: string) => m?.symptoms.find((x) => x.id === id)?.label ?? id;

  return (
    <section class="screen pcx" aria-labelledby="session-title">
      <div class="pc-row se-head">
        <h2 id="session-title" style="margin:0">
          Session: {s.conditions.trackName || "Untitled"}, {s.date}
        </h2>
        <span class="pc-grow" />
        <button type="button" class="pc-btn primary" onClick={() => setMode(mode === "log" ? "none" : "log")}>
          + LOG RUN
        </button>
        <button type="button" class="pc-btn" onClick={() => setMode(mode === "edit" ? "none" : "edit")}>
          Edit conditions
        </button>
        <button type="button" class="pc-btn" onClick={() => setShowSave(true)}>
          Save as setup...
        </button>
        <button type="button" class="pc-btn" onClick={() => setMode(mode === "new" ? "none" : "new")}>
          New session
        </button>
      </div>
      <p class="pc-muted">{conditionsSummary(s.conditions)}</p>
      {note && <p class="pc-ok pc-small">{note}</p>}
      {(err || bundleError.value) && (
        <p class="pc-err" role="alert">
          {err ?? bundleError.value}
        </p>
      )}

      {mode === "edit" && (
        <div class="pc-panel">
          <h3>Edit conditions</h3>
          <ConditionsForm
            initial={s.conditions}
            submitLabel="Save conditions"
            past={past}
            onSubmit={updateConditions}
            onCancel={() => setMode("none")}
          />
        </div>
      )}
      {mode === "new" && (
        <div class="pc-panel">
          <h3>New session</h3>
          <ConditionsForm
            initial={undefined}
            submitLabel="Start session"
            past={past}
            onSubmit={startSession}
            onCancel={() => setMode("none")}
          />
        </div>
      )}
      {mode === "log" && m && (
        <LogRunForm
          session={s}
          setup={currentSetup.value}
          symptoms={m.symptoms}
          runCount={runs.length}
          onCancel={() => setMode("none")}
          onLogged={async (run, newSetup) => {
            if (newSetup) currentSetup.value = newSetup;
            setMode("none");
            setNote(`Logged run ${run.seq}.`);
            await refreshBundle();
          }}
        />
      )}

      <div class="pc-panel">
        <h3>Runs</h3>
        {runsDesc.length === 0 && <p class="pc-muted">No runs yet. Tap + LOG RUN after your first pack.</p>}
        <ul class="se-list">
          {runsDesc.map((r) => (
            <li key={r.id} class="se-item">
              <div class="pc-row">
                <strong>Run {r.seq}</strong>
                <span>rating {r.rating ?? "not given"}</span>
                {typeof r.bestLapMs === "number" && <span>best lap {formatLap(r.bestLapMs)} s</span>}
                {r.lapTimesMs && r.lapTimesMs.length > 0 && <span class="pc-muted pc-small">{r.lapTimesMs.length} laps</span>}
                <span class="pc-muted pc-small">{timeOfDayLabel(r.createdAt)}</span>
              </div>
              <div class="pc-small">
                feel: {r.feel.length ? r.feel.map(feelLabel).join(", ") : "-"}
                {setupNote(r) && <span class="se-setupnote"> | setup: {setupNote(r)} (changed)</span>}
              </div>
              {r.notes && <div class="pc-small pc-muted">{r.notes}</div>}
              <div class="pc-row" style="margin-top:8px">
                <button type="button" class="pc-btn" onClick={() => openCompare(r)}>
                  What affected run {r.seq}?
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {runB && (
        <ComparePanel
          runs={runs}
          runA={runA}
          runB={runB}
          comparison={cmp}
          loading={cmpLoading}
          error={cmpErr}
          paramLabel={label}
          onPickA={setCmpA}
          onClose={() => {
            setCmpB(null);
            setCmpA(null);
          }}
        />
      )}

      <div class="pc-panel">
        <h3>Changes this session</h3>
        {changes.length === 0 && <p class="pc-muted">No setup changes yet. Edit values in Setup and commit.</p>}
        <ul class="se-list">
          {changes.map((c) => {
            const p = params.find((q) => q.id === c.param);
            return (
              <li key={c.id} class="se-item" data-testid="change-row">
                <div class="pc-row">
                  <span class="pc-muted pc-small">{timeOfDayLabel(c.createdAt)}</span>
                  <strong>{label(c.param)}</strong>
                  <span>
                    {formatValue(c.from, p?.unit)} to {formatValue(c.to, p?.unit)}
                  </span>
                  <span class="pc-muted pc-small">({c.source})</span>
                </div>
                <div class="pc-row" style="margin-top:8px">
                  <span class="pc-small">Outcome:</span>
                  {(["better", "same", "worse"] as Outcome[]).map((o) => (
                    <button
                      key={o}
                      type="button"
                      class="pc-chip"
                      aria-pressed={c.outcome === o}
                      onClick={() => void setOutcome(c, o)}
                    >
                      {o}
                    </button>
                  ))}
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      {showSave && (
        <SaveSetupDialog
          session={s}
          latestRunId={latest?.id}
          stagedCount={stagedCount()}
          onClose={() => setShowSave(false)}
          onSaved={(saved) => {
            setShowSave(false);
            setNote(`Saved "${saved.label}".`);
          }}
        />
      )}
    </section>
  );
}
