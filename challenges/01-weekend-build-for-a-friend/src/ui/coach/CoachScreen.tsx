// Coach screen (T4a, plan 5.1). Flow: tap a chip / say / type -> classified -> first checks -> one cited change
// -> Apply -> run laps -> Better / Same / Worse (-> revert offer).
// Space = push-to-talk while focus is not in a text field; Enter submits typed text.
import { useEffect, useState } from "preact/hooks";
import { Banner, Button, Card, CitationChip, Chip } from "../app/components";
import { openStartSession } from "../app/bootstrap";
import { explainerFor } from "../../scene";
import { llmStatus, meta, navigate, route, session, settings } from "../store";
import "./coach.css";
import { AskNotes } from "./AskNotes";
import { OutcomePanel } from "./OutcomePanel";
import { Prechecks } from "./Prechecks";
import { ScenePanel } from "./ScenePanel";
import { SuggestionCard } from "./SuggestionCard";
import { Thinking } from "./Thinking";
import {
  FALLBACK_CHIPS,
  currentOption,
  interim,
  listening,
  optionIndex,
  problemCheck,
  resetTurn,
  showAnyway,
  startListening,
  startTurn,
  stopListening,
  symptomLabel,
  turn,
  voiceHint,
} from "./state";

function chipList(): { id: string; label: string }[] {
  const fromMeta = meta.value?.symptoms.filter((s) => s.id !== "out-of-scope");
  if (!fromMeta?.length) return FALLBACK_CHIPS;
  const known = new Map(FALLBACK_CHIPS.map((c, i) => [c.id, { label: c.label, i }]));
  return fromMeta
    .map((s) => ({ id: s.id, label: known.get(s.id)?.label ?? s.label, i: known.get(s.id)?.i ?? 99 }))
    .sort((a, b) => a.i - b.i);
}

function isTextTarget(el: EventTarget | null): boolean {
  const n = el as HTMLElement | null;
  if (!n?.tagName) return false;
  return n.tagName === "INPUT" || n.tagName === "TEXTAREA" || n.tagName === "SELECT" || n.isContentEditable;
}

function ModelBanner() {
  const st = llmStatus.value;
  const s = settings.value;
  const toSettings = <Button onClick={() => navigate("settings")}>Settings</Button>;
  if (!st) return null;
  if (!st.reachable) {
    return (
      <Banner tone="warn" actions={toSettings}>
        <b>Coach phrasing is off:</b> Ollama not reachable. Chips and typed keywords still work.
      </Banner>
    );
  }
  if (!st.present) {
    return (
      <Banner tone="warn" actions={toSettings}>
        <b>Coach phrasing is off:</b> <code>{st.model}</code> is not pulled. Run <code>ollama pull {st.model}</code> or pull it in Settings. Chips and typed keywords still work.
      </Banner>
    );
  }
  if (s && !s.llmPhrasing) {
    return <Banner tone="info" actions={toSettings}>Coach phrasing is switched off in Settings, so the text below is the notes' own wording.</Banner>;
  }
  if (!st.loaded) {
    return <Banner tone="info">First answer after start can take longer while the model loads.</Banner>;
  }
  return null;
}

export function CoachScreen() {
  const [text, setText] = useState("");
  const t = turn.value;
  const s = session.value;
  const chips = chipList();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.code !== "Space" || route.value !== "coach" || isTextTarget(e.target) || e.ctrlKey || e.metaKey || e.altKey) return;
      e.preventDefault();
      if (!e.repeat) void startListening();
    };
    const up = (e: KeyboardEvent) => {
      if (e.code !== "Space" || route.value !== "coach" || isTextTarget(e.target)) return;
      e.preventDefault();
      stopListening();
    };
    addEventListener("keydown", down);
    addEventListener("keyup", up);
    return () => {
      removeEventListener("keydown", down);
      removeEventListener("keyup", up);
    };
  }, []);

  function submit() {
    const u = text.trim();
    if (!u) return;
    setText("");
    void startTurn({ utterance: u }, u);
  }

  const option = t ? currentOption(t) : null;
  const problem = problemCheck();
  const hideCard = !!problem && !showAnyway.value;
  const c = t?.classification;
  const alt = c && c.source !== "chip" && c.altId !== "none" ? c.altId : null;

  return (
    <section class="coach" aria-labelledby="coach-title">
      <h2 id="coach-title" class="sr-only">Coach</h2>

      {!s && (
        <Banner tone="info" actions={<Button variant="primary" onClick={openStartSession}>Start a session</Button>}>
          Start a practice session first so I know the track and your setup.
        </Banner>
      )}
      <ModelBanner />

      <div class="talk-row">
        <button
          type="button"
          class="btn btn-lg ptt"
          data-listening={listening.value}
          aria-pressed={listening.value}
          onPointerDown={(e) => {
            e.preventDefault();
            void startListening();
          }}
          onPointerUp={stopListening}
          onPointerLeave={() => listening.value && stopListening()}
          onKeyDown={(e) => e.key === "Enter" && void startListening()}
          onKeyUp={(e) => e.key === "Enter" && stopListening()}
        >
          {listening.value ? "LISTENING…" : "HOLD TO TALK"} <kbd>Space</kbd>
        </button>
        <input
          class="field grow"
          value={text}
          placeholder="type how the car feels, then press Enter"
          aria-label="Describe how the car feels"
          onInput={(e) => setText((e.target as HTMLInputElement).value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              submit();
            }
          }}
        />
        <Button variant="primary" size="lg" disabled={!text.trim()} onClick={submit}>
          Go
        </Button>
      </div>
      {listening.value && <p class="heard" aria-live="polite">Hearing: {interim.value || "…"}</p>}
      {voiceHint.value && !listening.value && <p class="muted small">{voiceHint.value}</p>}

      <div class="chip-row" role="group" aria-label="Quick symptoms">
        {chips.map((x) => (
          <Chip
            key={x.id}
            selected={t?.input.symptomId === x.id}
            onClick={() => void startTurn({ symptomId: x.id }, `Tapped: ${x.label}`)}
          >
            {x.label}
          </Chip>
        ))}
      </div>

      {t && (
        <div class="turn stack">
          <div class="heard-block">
            <p class="heard">
              {t.input.utterance ? <>Heard: "{t.heard}"</> : <>{t.heard}</>}
            </p>
            {c && t.status !== "refused" && (
              <p class="classified">
                &rarr; <b>{symptomLabel(c.symptomId)}</b>{" "}
                <span class="muted">({c.symptomId.replace(/-/g, " ")})</span>
                {c.source !== "chip" && (
                  <>
                    {" "}
                    <span class="muted">conf {c.confidence.toFixed(2)}</span>
                  </>
                )}
                {c.source !== "chip" && (
                  <span class="row inline">
                    <span class="muted">Not it?</span>
                    {alt && (
                      <Button size="md" onClick={() => void startTurn({ symptomId: alt }, `Tapped: ${symptomLabel(alt)}`)}>
                        {symptomLabel(alt)}
                      </Button>
                    )}
                    <Button size="md" variant="ghost" onClick={() => document.querySelector<HTMLElement>(".chip-row .chip")?.focus()}>
                      other
                    </Button>
                  </span>
                )}
              </p>
            )}
          </div>

          {t.status === "thinking" && <Thinking t={t} />}

          {t.status === "refused" && t.refusal && (
            <Card tone="muted" title="Not something my notes cover">
              <div class="stack">
                <p>{t.refusal.message}</p>
                {t.refusal.citations.length > 0 && (
                  <div class="row">
                    <span class="muted small">Why:</span>
                    {t.refusal.citations.map((cid) => (
                      <CitationChip key={cid} id={cid} />
                    ))}
                  </div>
                )}
                <div class="row">
                  <Button onClick={resetTurn}>Back to the chips</Button>
                </div>
              </div>
            </Card>
          )}

          {t.status === "error" && (
            <Banner tone="danger" actions={<Button onClick={resetTurn}>Dismiss</Button>}>
              <b>The coach hit a problem.</b> {t.error}
            </Banner>
          )}
          {t.status === "cancelled" && (
            <Banner tone="info" actions={<Button onClick={resetTurn}>Dismiss</Button>}>
              Cancelled. The card below is for reading only. Tap the symptom again to run it with the coach.
            </Banner>
          )}

          {t.status !== "refused" && <Prechecks t={t} />}

          {t.suggestion && !t.suggestion.primary && (
            <Card tone="muted" title="No change to suggest">
              <div class="stack">
                <p>{t.suggestion.noLeverReason ?? "Every option in my notes for this is at its limit or already tried."}</p>
                <div class="row">
                  <Button onClick={() => navigate("setup")}>Open Setup</Button>
                  <Button variant="ghost" onClick={resetTurn}>
                    Start over
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {option && !hideCard && (
            <div class="coach-grid">
              <div class="stack grow">
                <SuggestionCard t={t} option={option} />
                {(t.coachText || t.status === "thinking") && (
                  <div class="coach-says" aria-live="polite">
                    <span class="muted small">Coach says{t.explanation?.source === "template" ? " (notes' own wording)" : ""}:</span>
                    {optionIndex.value === 0 ? (
                      <p>{t.coachText || "…"}</p>
                    ) : (
                      <p class="muted">The coach phrased the first option only. The card above has this option's details.</p>
                    )}
                  </div>
                )}
              </div>
              {option.scene && explainerFor(option.scene.param) && <ScenePanel binding={option.scene} />}
            </div>
          )}

          <OutcomePanel t={t} />
        </div>
      )}

      {!t && s && <p class="muted">Tap what the car is doing, hold to talk, or type it. One change at a time.</p>}

      <AskNotes />
    </section>
  );
}
