// The "TRY ONE CHANGE" card (plan 5.1): one lever with its numbers, trade-off, check, citations, skipped levers.
// All values come from the server's LeverSuggestion (data/levers.json); the model only phrases the "Coach says" line.
import type { LeverSuggestion, SkipReason, Suggestion } from "../../shared/types";
import { Button, Card, CitationChip } from "../app/components";
import { meta } from "../store";
import { navigate } from "../store";
import {
  actionError,
  anotherOption,
  applyOption,
  busy,
  optionIndex,
  skipSuggestion,
  type TurnView,
} from "./state";

const REASON: Record<SkipReason, string> = {
  "at-limit": "already at the end of the range in my notes",
  "tried-worse": "you tried it and it got worse",
  "tried-same": "you tried it and nothing changed",
  "grip-mismatch": "it is for a different grip level",
  "draft-hidden": "not reviewed yet, and you hide unreviewed rows",
};

function leverLabel(id: string): string {
  return meta.value?.levers.find((l) => l.id === id)?.action ?? id;
}

function skippedLines(sug: Suggestion): string[] {
  const order: SkipReason[] = ["at-limit", "tried-worse", "tried-same", "grip-mismatch", "draft-hidden"];
  return [...sug.skipped]
    .sort((a, b) => order.indexOf(a.reason) - order.indexOf(b.reason))
    .slice(0, 3)
    .map((s) => `${leverLabel(s.leverId)}: ${REASON[s.reason]}`);
}

export function paramLabel(param: string | undefined): string {
  const label = (param && meta.value?.params.find((p) => p.id === param)?.label) || param || "";
  return label.replace(/\s*\(.*$/, ""); // "Rear shock position (1 laid down ...)" -> "Rear shock position"
}

export function ValueLine({ s }: { s: LeverSuggestion }) {
  const unit = s.lever.unit ? ` ${s.lever.unit}` : "";
  if (s.currentOutOfRange) {
    return (
      <p class="value-line value-hint">
        Your current {paramLabel(s.lever.param).toLowerCase()} ({String(s.from)}
        {unit}) looks outside the range in my notes; check it in Setup, then ask again for the exact number.
      </p>
    );
  }
  if (s.needsCurrentValue) {
    return (
      <p class="value-line value-hint">
        One step {s.lever.direction ?? "that way"}; enter your current {paramLabel(s.lever.param).toLowerCase()} in Setup for the exact number.
      </p>
    );
  }
  if (s.from === null || s.to === null) return null;
  return (
    <p class="value-line">
      <span class="muted">{paramLabel(s.lever.param)}</span>
      <span class="from">{String(s.from)}</span>
      <span aria-hidden="true">&rarr;</span>
      <span class="sr-only">to</span>
      <span class="to">
        {String(s.to)}
        {unit}
      </span>
    </p>
  );
}

export function SuggestionCard({ t, option }: { t: TurnView; option: LeverSuggestion }) {
  const sug = t.suggestion!;
  const idx = optionIndex.value;
  const total = 1 + sug.alternatives.length;
  const l = option.lever;
  // The runId arrives with the card (T7), so Apply works while the coach is still phrasing.
  const decidable = (t.status === "awaiting-decision" || t.status === "thinking") && !!t.runId;
  const closed = t.status === "awaiting-outcome" || (t.status === "done" && !!t.applied) || t.skipped;
  const numeric = !!l.param && !option.needsCurrentValue && option.to !== null;
  const lines = skippedLines(sug);
  return (
    <Card title={total > 1 ? `Try one change (option ${idx + 1} of ${total})` : "Try one change"} tone="accent" class="suggestion">
      <div class="stack">
        <div class="row">
          <h2 class="grow">{l.action}</h2>
          {l.status === "draft" && <span class="badge" title="The author has not reviewed this row yet">draft row (not reviewed)</span>}
        </div>
        <ValueLine s={option} />
        {actionError.value && <p class="err">{actionError.value}</p>}
        {closed ? (
          <div class="row card-actions">
            <span class="badge ok">{t.skipped ? "Skipped" : "Applied"}</span>
            {!t.skipped && <span class="muted small">Run your laps, then answer below.</span>}
          </div>
        ) : (
          <div class="row card-actions">
            {option.needsCurrentValue ? (
              <Button
                variant="primary"
                size="lg"
                onClick={() => navigate("setup", l.param ? { focus: l.param } : undefined)}
              >
                OPEN SETUP
              </Button>
            ) : (
              <Button variant="primary" size="lg" disabled={!decidable || busy.value} onClick={() => void applyOption()}>
                {numeric ? "APPLY" : "I DID IT"}
              </Button>
            )}
            <Button size="lg" disabled={total < 2 || busy.value} onClick={anotherOption}>
              ANOTHER OPTION
            </Button>
            <Button size="lg" variant="ghost" disabled={!decidable || busy.value} onClick={() => void skipSuggestion()}>
              SKIP
            </Button>
          </div>
        )}
        {!closed && !decidable && t.status === "thinking" && <p class="muted small">Apply unlocks in a moment.</p>}
        {/* Once applied or skipped, the card shrinks to what matters for the laps (Check / Then), so the
            Better / Same / Worse buttons below stay on the first screen (T12). */}
        {!closed && <p>{l.effect}</p>}
        {!closed && (
          <p>
            <b>Trade-off:</b> {l.tradeOff}
          </p>
        )}
        <p>
          <b>Check:</b> {l.verify}
        </p>
        {l.followUp && (
          <p class="muted">
            <b>Then:</b> {l.followUp}
          </p>
        )}
        {l.citations.length > 0 && !closed && (
          <div class="row" aria-label="Notes behind this">
            <span class="muted small">Notes:</span>
            {l.citations.map((c) => (
              <CitationChip key={c} id={c} />
            ))}
          </div>
        )}
        {lines.length > 0 && idx === 0 && !closed && (
          <p class="muted small">
            <b>Not picked:</b> {lines.join(" · ")}
          </p>
        )}
      </div>
    </Card>
  );
}
