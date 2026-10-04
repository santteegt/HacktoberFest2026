// Race day screen (T4c, plan 5.4): today's conditions, ranked saved setups (score bar, reasons, [Load], [Compare]),
// an "Other surface" group, and "What has worked for you" from the driver's own outcome taps.
// Load stages the setup differences in the Setup screen as manual changes; nothing is written until he commits there.
import { useEffect, useMemo, useState } from "preact/hooks";
import { getHistory, getSimilar, listSessions, patchSession } from "../../api/client";
import type { ParamDef, ParamHistoryRow, Session, SimilarHit, TrackConditions } from "../../shared/types";
import { Banner, Button, Card, CitationChip } from "../app/components";
import { ConditionsForm } from "../session/ConditionsForm";
import { conditionsSummary } from "../setup/SaveSetupDialog";
import { deltaText, formatValue } from "../setup/logic";
import { bindStagedToSession, stage } from "../setup/staged";
import { errorMessage } from "../setup/widgets";
import "../setup/widgets.css";
import { currentSetup, meta, navigate, session } from "../store";
import {
  HISTORY_LABEL,
  WEIGHTS_TEXT,
  directionWord,
  historySummary,
  loadableDiff,
  paramCountText,
  splitHits,
  tryWord,
} from "./logic";
import "./race.css";

const SURFACE_SPLIT_CITE = "yokomo-bd12#real-driver-setup-sheets-exist-for-this-exact-ch";

function todayTags(c: TrackConditions): { text: string; kind?: string }[] {
  const tags: { text: string; kind?: string }[] = [
    { text: c.trackName || "(no track name)" },
    { text: c.surface },
    { text: `${c.grip} grip` },
    { text: c.bumpy ? "bumpy" : "smooth" },
  ];
  if (c.layout) tags.push({ text: `${c.layout} layout` });
  if (typeof c.trackTempC === "number") tags.push({ text: `track ${c.trackTempC} C` });
  if (typeof c.airTempC === "number") tags.push({ text: `air ${c.airTempC} C` });
  if (c.timeOfDay) tags.push({ text: c.timeOfDay });
  return tags;
}

export function RaceScreen() {
  const s = session.value;
  const m = meta.value;
  const params = m?.params ?? [];
  const [hits, setHits] = useState<SimilarHit[] | null>(null);
  const [history, setHistory] = useState<ParamHistoryRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [histErr, setHistErr] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [past, setPast] = useState<Session[]>([]);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [helpOpen, setHelpOpen] = useState(false);
  const [loadNote, setLoadNote] = useState<string | null>(null);
  const condKey = s ? JSON.stringify(s.conditions) : "";

  useEffect(() => {
    if (!s) {
      setHits(null);
      return;
    }
    let live = true;
    setErr(null);
    getSimilar(s.id)
      .then((h) => live && setHits(h))
      .catch((e) => live && (setHits([]), setErr(errorMessage(e))));
    return () => {
      live = false;
    };
  }, [s?.id, condKey]);

  useEffect(() => {
    let live = true;
    getHistory()
      .then((h) => live && (setHistory(h), setHistErr(null)))
      .catch((e) => live && (setHistory([]), setHistErr(errorMessage(e))));
    listSessions()
      .then((l) => live && setPast(l))
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [s?.id]);

  const label = (id: string): ParamDef | undefined => params.find((p) => p.id === id);
  const groups = useMemo(() => splitHits(hits ?? []), [hits]);

  function load(h: SimilarHit) {
    if (!s) return;
    const diff = loadableDiff(h.diffVsCurrent, params);
    bindStagedToSession(s.id);
    const committed = currentSetup.value?.values ?? {};
    for (const d of diff) stage(d.param, d.to, committed);
    setLoadNote(
      diff.length === 0
        ? `"${h.saved.label}" has the same settings as now; nothing to stage.`
        : `Staged ${diff.length} change${diff.length === 1 ? "" : "s"} from "${h.saved.label}" in Setup.`,
    );
    navigate("setup");
  }

  async function saveConditions(c: TrackConditions) {
    if (!s) return;
    const next = await patchSession(s.id, { conditions: c });
    session.value = next;
    setEditing(false);
  }

  return (
    <section class="screen" aria-labelledby="race-title">
      <div class="rd-head">
        <h2 id="race-title">Race day</h2>
        <span class="rd-note">Which saved setup fits today's track?</span>
      </div>

      {!s ? (
        <Card class="rd-first" title="Today's conditions">
          <p>No session is open. Race day ranks your saved setups against the conditions of the open session.</p>
          <div class="row" style="margin-top:12px">
            <Button variant="primary" onClick={() => navigate("session")}>
              Start a session
            </Button>
          </div>
        </Card>
      ) : (
        <Card title="Today's conditions">
          <div class="rd-today" data-testid="today-conditions">
            {todayTags(s.conditions).map((t) => (
              <span class="rd-tag" key={t.text}>
                {t.text}
              </span>
            ))}
            <Button onClick={() => setEditing((v) => !v)} aria-expanded={editing}>
              {editing ? "Close" : "Edit conditions"}
            </Button>
          </div>
          <p class="rd-note" style="margin-top:8px">
            Prefilled from the open session ({s.date}). Editing updates that session's conditions, then the ranking refreshes.
          </p>
          {editing && (
            <div class="pcx rd-edit">
              <ConditionsForm initial={s.conditions} past={past} submitLabel="Update ranking" onSubmit={saveConditions} onCancel={() => setEditing(false)} />
            </div>
          )}
        </Card>
      )}

      {err && (
        <Banner tone="danger" class="rd-banner">
          Could not rank saved setups: {err}
        </Banner>
      )}
      {loadNote && !err && (
        <Banner tone="ok" class="rd-banner">
          {loadNote}
        </Banner>
      )}

      <div class="rd-layout">
        <div>
          <Card title="Saved setups for these conditions">
            <div class="row" style="margin-bottom:12px">
              <Button aria-expanded={helpOpen} aria-controls="rd-weights" onClick={() => setHelpOpen((v) => !v)} title={WEIGHTS_TEXT}>
                ? How is the score worked out
              </Button>
            </div>
            {helpOpen && (
              <p id="rd-weights" class="rd-help" data-testid="weights-help">
                {WEIGHTS_TEXT}
              </p>
            )}

            {!s && <p class="muted">Start or open a session to rank your saved setups against its conditions.</p>}
            {s && hits === null && <p class="muted">Looking through your saved setups...</p>}
            {hits !== null && hits.length === 0 && !err && (
              <p data-testid="race-empty">No saved setups yet. Save one from a practice session that went well.</p>
            )}

            {groups.same.length > 0 && (
              <div class="rd-group" data-testid="group-same">
                <ol class="rd-list">
                  {groups.same.map((h) => (
                    <HitCard key={h.saved.id} hit={h} params={params} open={!!open[h.saved.id]} onToggle={() => setOpen({ ...open, [h.saved.id]: !open[h.saved.id] })} onLoad={() => load(h)} label={label} />
                  ))}
                </ol>
              </div>
            )}
            {hits !== null && hits.length > 0 && groups.same.length === 0 && (
              <p class="muted">Nothing saved on {s?.conditions.surface} yet.</p>
            )}

            {groups.other.length > 0 && (
              <div class="rd-group" data-testid="group-other">
                <h3 class="rd-group-title">
                  Other surface
                  <CitationChip id={SURFACE_SPLIT_CITE} label="why separate" />
                </h3>
                <p class="rd-note" style="margin-bottom:12px">
                  Saved on a different surface from today's, so they never rank above a matching one. Setup sheets for this car are split by surface in the notes.
                </p>
                <ol class="rd-list">
                  {groups.other.map((h) => (
                    <HitCard key={h.saved.id} hit={h} params={params} open={!!open[h.saved.id]} onToggle={() => setOpen({ ...open, [h.saved.id]: !open[h.saved.id] })} onLoad={() => load(h)} label={label} />
                  ))}
                </ol>
              </div>
            )}
          </Card>
        </div>

        <Card title="What has worked for you" class="rd-history" aria-label="What has worked for you">
          <p class="rd-note" style="margin-bottom:8px">
            From the outcomes you tapped after changes ({HISTORY_LABEL}).
          </p>
          {histErr && <p class="rd-err">Could not load history: {histErr}</p>}
          {history && history.length === 0 && !histErr && (
            <p class="muted" data-testid="history-empty">
              Nothing yet. Tap better, same or worse after a change and it shows up here.
            </p>
          )}
          {history && history.length > 0 && (
            <table class="rd-hist" data-testid="history-table">
              <thead>
                <tr>
                  <th>Change</th>
                  <th>Outcomes</th>
                </tr>
              </thead>
              <tbody>
                {history.map((r) => (
                  <tr key={`${r.param}|${r.direction}`}>
                    <td>
                      <b>{label(r.param)?.label ?? r.param}</b>
                      <br />
                      <span class="muted small">
                        {directionWord(r.direction)}, {tryWord(r.tries)}
                      </span>
                    </td>
                    <td>
                      {historySummary(r)}
                      <br />
                      <span class="muted small">{r.label || HISTORY_LABEL}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </section>
  );
}

function HitCard(props: {
  hit: SimilarHit;
  params: ParamDef[];
  open: boolean;
  onToggle: () => void;
  onLoad: () => void;
  label: (id: string) => ParamDef | undefined;
}) {
  const { hit: h } = props;
  const diff = loadableDiff(h.diffVsCurrent, props.params);
  const score = Math.max(0, Math.min(100, h.score));
  return (
    <li class="rd-hit" data-testid="hit" data-other={h.surfaceMismatch ? "1" : "0"}>
      <div class="rd-hit-top">
        <div>
          <div class="rd-hit-title">{h.saved.label}</div>
          <div class="muted small">
            {conditionsSummary(h.saved.conditions)} | saved {new Date(h.saved.createdAt).toLocaleDateString()}
            {h.saved.eventName ? ` | ${h.saved.eventName}` : ""}
          </div>
          {h.saved.verdict && <div class="small">Your note: {h.saved.verdict}</div>}
        </div>
        <div class="rd-score" aria-label={`Match ${Math.round(score)} out of 100`}>
          <div class="rd-bar" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(score)} data-other={h.surfaceMismatch ? "1" : "0"}>
            <i style={`width:${score}%`} />
          </div>
          <b data-testid="score">{Math.round(score)}</b>
        </div>
      </div>
      <div class="row" aria-label="Why it ranks here">
        {h.reasons.map((r) => (
          <span class="rd-tag" data-kind={h.surfaceMismatch && /surface/.test(r) ? "warn" : "reason"} key={r}>
            {r}
          </span>
        ))}
      </div>
      <div class="rd-actions">
        <span data-testid="differs">{paramCountText(diff.length)}</span>
        <Button variant="primary" onClick={props.onLoad} disabled={diff.length === 0} title="Stage these differences in Setup (nothing is saved until you commit there)">
          Load
        </Button>
        <Button onClick={props.onToggle} aria-expanded={props.open}>
          {props.open ? "Hide" : "Compare"}
        </Button>
      </div>
      {props.open && (
        <div>
          {diff.length === 0 ? (
            <p class="rd-ok">Identical to your current setup.</p>
          ) : (
            <table class="rd-table">
              <thead>
                <tr>
                  <th>Setting</th>
                  <th>Now</th>
                  <th>Saved</th>
                  <th>To get there</th>
                </tr>
              </thead>
              <tbody>
                {diff.map((d) => {
                  const p = props.label(d.param);
                  return (
                    <tr key={d.param}>
                      <td>{p?.label ?? d.param}</td>
                      <td>{formatValue(d.from, p?.unit)}</td>
                      <td>{formatValue(d.to, p?.unit)}</td>
                      <td>{deltaText(d.from, d.to) || directionWord(d.direction)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}
    </li>
  );
}
