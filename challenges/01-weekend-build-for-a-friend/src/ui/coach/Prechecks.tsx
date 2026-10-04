// Pre-check gate (plan 4.4): big OK / "Found a problem" toggles above the card. The gate never blocks:
// "Already checked" skips it, and a problem only adds a "fix that first" banner and a session note.
import { Banner, Button, Card, CitationChip, Chip } from "../app/components";
import {
  markPrecheck,
  precheckMarks,
  prechecksSkipped,
  problemCheck,
  showAnyway,
  type TurnView,
} from "./state";

export function Prechecks({ t }: { t: TurnView }) {
  if (!t.prechecks.length) return null;
  if (prechecksSkipped.value) {
    return (
      <div class="row">
        <span class="muted">First checks skipped.</span>
        <Button variant="ghost" onClick={() => (prechecksSkipped.value = false)}>
          Show the checks
        </Button>
      </div>
    );
  }
  const problem = problemCheck();
  return (
    <div class="stack">
      <div class="row">
        <h3 class="grow">First check</h3>
        <Button onClick={() => (prechecksSkipped.value = true)}>Already checked</Button>
      </div>
      <div class="check-grid">
        {t.prechecks.map((p) => {
          const mark = precheckMarks.value[p.id];
          return (
            <Card key={p.id} class="check" tone={mark === "problem" ? "accent" : undefined}>
              <div class="check-head">
                <div class="check-label grow">{p.label}</div>
                <div class="row">
                <Chip selected={mark === "ok"} tone="ok" onClick={() => markPrecheck(p.id, "ok")}>
                  OK
                </Chip>
                <Chip selected={mark === "problem"} tone="danger" onClick={() => markPrecheck(p.id, "problem")}>
                  Found a problem
                </Chip>
                </div>
              </div>
              <div class="muted small">{p.detail}</div>
              {p.citations.length > 0 && (
                <div class="row">
                  {p.citations.slice(0, 1).map((c) => (
                    <CitationChip key={c} id={c} />
                  ))}
                </div>
              )}
            </Card>
          );
        })}
      </div>
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
