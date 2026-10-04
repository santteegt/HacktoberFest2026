// Pre-check gate (plan 4.4), compact form (T12): one row above the card ("3 quick checks: Belts, Tyres, ...")
// with a single "All OK" button and an expand control to mark each item or flag a problem. The gate never
// blocks: "All OK" clears it, and a problem only adds a "fix that first" banner and a session note.
import { useState } from "preact/hooks";
import { Banner, Button, CitationChip, Chip } from "../app/components";
import {
  markPrecheck,
  precheckMarks,
  prechecksSkipped,
  problemCheck,
  showAnyway,
  type TurnView,
} from "./state";

export function Prechecks({ t }: { t: TurnView }) {
  const [open, setOpen] = useState(false);
  if (!t.prechecks.length) return null;
  if (prechecksSkipped.value) {
    return (
      <div class="checks-bar" data-state="skipped">
        <span class="muted grow">First checks skipped.</span>
        <Button variant="ghost" onClick={() => (prechecksSkipped.value = false)}>
          Show the checks
        </Button>
      </div>
    );
  }
  const marks = precheckMarks.value;
  const problem = problemCheck();
  const n = t.prechecks.length;
  const allOk = t.prechecks.every((p) => marks[p.id] === "ok");
  const listId = `checks-${t.localId}`;
  const allOkNow = () => {
    for (const p of t.prechecks) markPrecheck(p.id, "ok");
    setOpen(false);
  };
  const state = problem ? "problem" : allOk ? "ok" : "open";
  return (
    <div class="stack checks">
      <div class="checks-bar" data-state={state}>
        <div class="checks-summary grow">
          <b>{allOk ? `${n} quick checks: all OK` : problem ? `${n} quick checks: problem found` : `${n} quick checks first`}</b>
          <span class="checks-names">
            {t.prechecks.map((p) => (
              <span key={p.id} class="check-name" data-mark={marks[p.id] ?? "none"}>
                {p.label}
              </span>
            ))}
          </span>
        </div>
        {!allOk && !problem && (
          <Button onClick={allOkNow} title="All of these are fine, or you already checked them">
            All OK
          </Button>
        )}
        <Button variant="ghost" aria-expanded={open} aria-controls={listId} onClick={() => setOpen(!open)}>
          {open ? "Hide checks" : "Check each"}
        </Button>
      </div>
      {open && (
        <ul class="check-list" id={listId}>
          {t.prechecks.map((p) => {
            const mark = marks[p.id];
            return (
              <li key={p.id} class="check" data-mark={mark ?? "none"}>
                <div class="check-text">
                  <div class="check-label">{p.label}</div>
                  <div class="muted small">{p.detail}</div>
                </div>
                <div class="check-actions">
                  {p.citations.slice(0, 1).map((c) => (
                    <CitationChip key={c} id={c} />
                  ))}
                  <Chip selected={mark === "ok"} tone="ok" onClick={() => markPrecheck(p.id, "ok")}>
                    OK
                  </Chip>
                  <Chip selected={mark === "problem"} tone="danger" onClick={() => markPrecheck(p.id, "problem")}>
                    Problem
                  </Chip>
                </div>
              </li>
            );
          })}
        </ul>
      )}
      {problem && (
        <Banner
          tone="warn"
          actions={
            <Button onClick={() => (showAnyway.value = !showAnyway.value)}>
              {showAnyway.value ? "Hide the suggestion" : "Show the suggestion anyway"}
            </Button>
          }
        >
          <b>Fix that first, then run again:</b> {problem.label}. {problem.detail} <span class="muted">(Noted in this session.)</span>
        </Banner>
      )}
    </div>
  );
}
