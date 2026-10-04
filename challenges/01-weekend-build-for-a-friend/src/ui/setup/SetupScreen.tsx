// Setup editor (T4b, plan 5.2): every parameter group, baseline vs current vs signed delta, stepper buttons,
// staged changes (amber) with Commit and Undo, save-as-setup, compare with a saved setup, explainer slot.
import { useEffect, useState } from "preact/hooks";
import { request } from "../../api/client";
import type { ParamDef, ParamGroup, ParamValue, SavedSetup, SetupValues } from "../../shared/types";
import { bundle, ensureBundle, refreshBundle } from "../session/bundle";
import { currentSetup, meta, routeQuery, session } from "../store";
import { CompareSaved } from "./CompareSaved";
import { ExplainerPanel } from "./ExplainerPanel";
import { SaveSetupDialog, conditionsSummary } from "./SaveSetupDialog";
import {
  baselineOf,
  computeFdr,
  conventionKey,
  deltaMeaning,
  deltaText,
  formatValue,
  isOutOfRange,
  parseNumberInput,
  rangeText,
  rangeUnsourced,
  sameValue,
  stepValue,
} from "./logic";
import { bindStagedToSession, canUndo, clearStaged, discardAll, effectiveValues, stage, staged, undoLast } from "./staged";
import { errorMessage } from "./widgets";
import "./setup.css";

const GROUP_ORDER: ParamGroup[] = ["alignment", "chassis", "steering", "damping", "drivetrain", "aero", "tyres"];
const GROUP_LABEL: Record<ParamGroup, string> = {
  alignment: "Alignment",
  chassis: "Chassis",
  steering: "Steering",
  damping: "Springs, dampers and bars",
  drivetrain: "Drivetrain",
  aero: "Body and wheels",
  tyres: "Tyres",
};

export function SetupScreen() {
  const m = meta.value;
  const s = session.value;
  const cur = currentSetup.value;
  const [changedOnly, setChangedOnly] = useState(false);
  const [openRow, setOpenRow] = useState<string | null>(null);
  const [explainId, setExplainId] = useState<string | null>(null);
  const [showSave, setShowSave] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [savedNote, setSavedNote] = useState<string | null>(null);
  const [savedTick, setSavedTick] = useState(0);

  useEffect(() => {
    bindStagedToSession(s?.id ?? null);
    void ensureBundle();
  }, [s?.id]);

  // "#/setup?focus=<paramId>" (OPEN SETUP on a coach card, T10): show that row, scroll it into view,
  // highlight it for a few seconds and put the cursor in its value field.
  const focusId = routeQuery.value.focus ?? null;
  const [flashId, setFlashId] = useState<string | null>(null);
  const ready = !!m && !!s;
  useEffect(() => {
    if (!focusId || !ready) return;
    setChangedOnly(false);
    setFlashId(focusId);
    const raf = requestAnimationFrame(() => {
      const row = document.querySelector<HTMLElement>(`[data-param="${CSS.escape(focusId)}"]`);
      if (!row) return;
      row.scrollIntoView({ block: "center" });
      row.querySelector<HTMLInputElement>("input")?.focus({ preventScroll: true });
    });
    const t = setTimeout(() => setFlashId(null), 4000);
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(t);
    };
  }, [focusId, ready]);

  if (!m) {
    return (
      <section class="screen pcx" aria-labelledby="setup-title">
        <h2 id="setup-title">Setup</h2>
        <p class="pc-muted">Loading the parameter list...</p>
      </section>
    );
  }
  if (!s) {
    return (
      <section class="screen pcx" aria-labelledby="setup-title">
        <h2 id="setup-title">Setup</h2>
        <div class="pc-panel">
          <p>Start a practice session first: setup changes are logged against a session.</p>
          <a class="pc-btn primary" href="#/session" style="display:inline-flex;align-items:center;text-decoration:none">
            Go to Session
          </a>
        </div>
      </section>
    );
  }

  const params = m.params;
  const committed: SetupValues = cur?.values ?? {};
  const overlay = staged.value;
  const effective = effectiveValues(committed, overlay);
  const stagedIds = Object.keys(overlay);
  const latestRun = bundle.value?.runs.length ? bundle.value.runs[bundle.value.runs.length - 1] : undefined;

  const isChanged = (p: ParamDef) => {
    const base = baselineOf(p).value;
    return !sameValue(effective[p.id] ?? null, base);
  };

  async function commit() {
    if (!s || !stagedIds.length) return;
    setBusy(true);
    setErr(null);
    try {
      const values: SetupValues = {};
      for (const id of stagedIds) values[id] = overlay[id];
      const res = await request("POST /api/sessions/:id/setup", { values, source: "manual" }, { params: { id: s.id } });
      currentSetup.value = res.setup;
      session.value = { ...s, currentSetupId: res.setup.id };
      clearStaged();
      setSavedNote(`Committed ${res.changes.length} change${res.changes.length === 1 ? "" : "s"}.`);
      await refreshBundle();
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  const visible = (p: ParamDef) => !changedOnly || isChanged(p);
  const explainParam = explainId ? (params.find((p) => p.id === explainId) ?? null) : null;

  return (
    <section class="screen pcx su-screen" aria-labelledby="setup-title">
      <div class="su-main">
        <div class="pc-row su-head">
          <h2 id="setup-title" style="margin:0">
            Setup ({m.car === "yokomo-bd12" ? "BD12" : "generic"})
          </h2>
          <div class="pc-chips" role="group" aria-label="Show parameters">
            <button type="button" class="pc-chip" aria-pressed={!changedOnly} onClick={() => setChangedOnly(false)}>
              All
            </button>
            <button type="button" class="pc-chip" aria-pressed={changedOnly} onClick={() => setChangedOnly(true)}>
              Changed only
            </button>
          </div>
        </div>
        <p class="pc-small pc-muted">{conditionsSummary(s.conditions)}. Baseline: {m.baselineRule.split(" Source:")[0]}</p>

        <div class="su-stagebar" data-staged={stagedIds.length > 0 ? "1" : "0"} role="status">
          <span>
            Staged: <strong>{stagedIds.length}</strong> change{stagedIds.length === 1 ? "" : "s"}
          </span>
          <button type="button" class="pc-btn warn" disabled={!stagedIds.length || busy} onClick={commit}>
            {busy ? "Committing..." : "Commit"}
          </button>
          <button type="button" class="pc-btn" disabled={!canUndo()} onClick={undoLast}>
            Undo
          </button>
          <button type="button" class="pc-btn" disabled={!stagedIds.length} onClick={discardAll}>
            Discard all
          </button>
          {savedNote && !stagedIds.length && <span class="pc-ok pc-small">{savedNote}</span>}
        </div>
        {err && <p class="pc-err" role="alert">{err}</p>}

        {GROUP_ORDER.map((g) => {
          const rows = params.filter((p) => p.group === g && visible(p));
          if (!rows.length) return null;
          return (
            <div class="pc-panel su-group" key={g}>
              <h3>{GROUP_LABEL[g]}</h3>
              <div class="su-colhead pc-small pc-muted" aria-hidden="true">
                <span>Setting</span>
                <span>Baseline</span>
                <span>Current</span>
                <span>Change</span>
              </div>
              {rows.map((p) => (
                <ParamRow
                  key={p.id}
                  p={p}
                  params={params}
                  committed={committed}
                  effective={effective}
                  convention={(() => {
                    const k = conventionKey(p.id);
                    return k ? m.conventions[k] : undefined;
                  })()}
                  open={openRow === p.id}
                  onToggle={() => setOpenRow(openRow === p.id ? null : p.id)}
                  onExplain={() => setExplainId(p.id)}
                  explained={explainId === p.id}
                  flash={flashId === p.id}
                />
              ))}
            </div>
          );
        })}
        {changedOnly && !params.some((p) => isChanged(p)) && (
          <p class="pc-muted">Nothing differs from the baseline yet.</p>
        )}

        <div class="pc-row su-actions">
          <button type="button" class="pc-btn primary" onClick={() => setShowSave(true)}>
            Save as setup...
          </button>
        </div>
        <CompareSaved params={params} current={effective} refreshKey={savedTick} />
      </div>

      <div class="su-side" data-open={explainParam ? "1" : "0"}>
        <ExplainerPanel
          param={explainParam}
          committed={committed}
          effective={effective}
          conventions={m.conventions}
          onClose={() => setExplainId(null)}
        />
      </div>

      {showSave && (
        <SaveSetupDialog
          session={s}
          latestRunId={latestRun?.id}
          stagedCount={stagedIds.length}
          onClose={() => setShowSave(false)}
          onSaved={(saved: SavedSetup) => {
            setShowSave(false);
            setSavedTick((n) => n + 1);
            setSavedNote(`Saved "${saved.label}".`);
          }}
        />
      )}
    </section>
  );
}

function ParamRow(props: {
  p: ParamDef;
  params: ParamDef[];
  committed: SetupValues;
  effective: SetupValues;
  convention?: string;
  open: boolean;
  onToggle: () => void;
  onExplain: () => void;
  explained: boolean;
  flash?: boolean;
}) {
  const { p, committed, effective } = props;
  const base = baselineOf(p);
  const eff = effective[p.id] ?? null;
  const com = committed[p.id] ?? null;
  const isStaged = !sameValue(eff, com);
  const changed = !sameValue(eff, base.value);
  const out = isOutOfRange(p, eff);
  const hasExplainer = Boolean(p.explainer);
  const [draft, setDraft] = useState<string | null>(null);
  const [bad, setBad] = useState(false);

  const setValue = (v: ParamValue) => stage(p.id, v, committed);

  // Reads the text from the event target (not the draft state) so a blur right after typing never sees a stale draft.
  function applyDraft(e: Event) {
    const text = (e.target as HTMLInputElement).value;
    if (draft === null && text === (eff === null || eff === undefined ? "" : String(eff))) return;
    if (p.kind === "text") {
      setValue(text.trim() === "" ? null : text.trim());
    } else {
      const n = parseNumberInput(text);
      if (Number.isNaN(n)) {
        setBad(true);
        setDraft(null);
        return;
      }
      setValue(n);
    }
    setBad(false);
    setDraft(null);
  }

  // Computed row (FDR).
  if (p.kind === "computed") {
    const fdr = computeFdr(props.params, effective);
    const baseFdr = computeFdr(props.params, Object.fromEntries(props.params.map((x) => [x.id, baselineOf(x).value])));
    return (
      <div class="su-row" data-changed="0">
        <div class="su-label">
          <span class="su-name">{p.label}</span>
          <span class="pc-small pc-muted">Read only. {p.formula ? `Formula: ${p.formula}` : ""}</span>
        </div>
        <div class="su-base">{baseFdr === null ? "-" : baseFdr}</div>
        <div class="su-cur">
          <strong class="su-fdr">{fdr === null ? "enter spur and pinion" : fdr}</strong>
          <span class="pc-small pc-muted"> computed</span>
        </div>
        <div class="su-delta" />
      </div>
    );
  }

  const display = draft ?? (eff === null || eff === undefined ? "" : String(eff));
  const delta = changed ? deltaText(base.value, eff) : "";
  const meaning = changed ? deltaMeaning(p, base.value, eff) : "";

  return (
    <div
      class="su-row"
      data-param={p.id}
      data-focus={props.flash ? "1" : "0"}
      data-changed={changed ? "1" : "0"}
      data-staged={isStaged ? "1" : "0"}
      data-out={out ? "1" : "0"}
    >
      <div class="su-label">
        <span class="su-name">{p.label}</span>
        {props.convention && <span class="pc-small pc-muted">{props.convention}</span>}
        <span class="pc-small">
          {rangeText(p) && <span class="pc-muted">range {rangeText(p)}</span>}
          {rangeUnsourced(p) && <span class="su-unsourced"> range: unsourced</span>}
        </span>
        {out && <span class="pc-flag">outside the range in my notes</span>}
        <span class="su-btns">
          <button
            type="button"
            class="pc-btn su-q"
            aria-expanded={props.open}
            aria-label={`About ${p.label}`}
            onClick={props.onToggle}
          >
            ?
          </button>
          {hasExplainer && (
            <button
              type="button"
              class="pc-btn su-q"
              aria-pressed={props.explained}
              aria-label={`Show ${p.label} on the car`}
              onClick={props.onExplain}
            >
              Car
            </button>
          )}
        </span>
      </div>

      <div class="su-base">
        {base.value === null ? <span class="pc-muted">not set</span> : String(base.value)}
        {base.generic && <span class="su-tag"> generic</span>}
      </div>

      <div class="su-cur">
        {p.kind === "enum" && p.options ? (
          <div class="pc-chips" role="radiogroup" aria-label={p.label}>
            {p.options.map((o) => (
              <button
                key={o}
                type="button"
                role="radio"
                class="pc-chip"
                aria-checked={eff === o}
                data-staged={isStaged && eff === o ? "1" : "0"}
                onClick={() => setValue(eff === o ? null : o)}
              >
                {o}
              </button>
            ))}
          </div>
        ) : p.kind === "text" ? (
          <input
            type="text"
            aria-label={p.label}
            value={display}
            data-staged={isStaged ? "1" : "0"}
            onInput={(e) => setDraft((e.target as HTMLInputElement).value)}
            onBlur={applyDraft}
            onKeyDown={(e) => e.key === "Enter" && applyDraft(e)}
          />
        ) : (
          <div class="su-stepper">
            <button
              type="button"
              class="pc-btn"
              aria-label={`Decrease ${p.label}`}
              onClick={() => setValue(stepValue(p, eff, -1))}
            >
              -
            </button>
            <input
              type="text"
              inputMode="decimal"
              aria-label={p.label}
              value={display}
              placeholder={p.unit || "value"}
              data-staged={isStaged ? "1" : "0"}
              onInput={(e) => setDraft((e.target as HTMLInputElement).value)}
              onBlur={applyDraft}
              onKeyDown={(e) => e.key === "Enter" && applyDraft(e)}
            />
            <button
              type="button"
              class="pc-btn"
              aria-label={`Increase ${p.label}`}
              onClick={() => setValue(stepValue(p, eff, 1))}
            >
              +
            </button>
            <span class="pc-small pc-muted su-unit">{p.unit}</span>
          </div>
        )}
        {bad && <span class="pc-err">Not a number</span>}
        {isStaged && (
          <span class="su-was pc-small">staged, was {formatValue(com, p.unit)}</span>
        )}
      </div>

      <div class="su-delta">
        {delta && (
          <span class="su-badge" data-staged={isStaged ? "1" : "0"}>
            {delta}
          </span>
        )}
        {meaning && <span class="pc-small pc-muted">{meaning}</span>}
        {changed && !delta && <span class="su-badge">changed</span>}
      </div>

      {props.open && (
        <div class="su-detail pc-small">
          {props.convention && (
            <p>
              <strong>Sign convention:</strong> {props.convention}
            </p>
          )}
          <p>
            <strong>Range source:</strong> {p.range}
          </p>
          {p.step !== undefined && (
            <p>
              <strong>Step:</strong> {p.step} {p.unit}
            </p>
          )}
          {p.src.length > 0 && (
            <p>
              <strong>Notes:</strong> {p.src.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
