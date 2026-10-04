// After APPLY: Better / Same / Worse, then the follow-up the server asks for (save-setup, next-lever, offer-revert).
import { useState } from "preact/hooks";
import { saveSetup } from "../../api/client";
import { Banner, Button, Card } from "../app/components";
import { session } from "../store";
import { navigate } from "../store";
import { paramLabel } from "./SuggestionCard";
import { busy, actionError, resetTurn, revertChange, sendOutcome, startTurn, symptomLabel, type TurnView } from "./state";

function SaveInline() {
  const s = session.value;
  const [label, setLabel] = useState(s ? `${s.conditions.trackName} ${s.date}` : "");
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [err, setErr] = useState("");
  if (!s) return null;
  if (state === "saved") return <span class="badge ok">Saved. Find it under Race day.</span>;
  async function save() {
    setState("saving");
    try {
      await saveSetup({ label: label.trim() || "Saved setup", setupId: s!.currentSetupId, conditions: s!.conditions, sessionId: s!.id });
      setState("saved");
    } catch (e) {
      setErr((e as Error).message);
      setState("error");
    }
  }
  return (
    <div class="row">
      <input class="field grow" value={label} aria-label="Name for the saved setup" onInput={(e) => setLabel((e.target as HTMLInputElement).value)} />
      <Button variant="ok" disabled={state === "saving"} onClick={save}>
        Save this setup
      </Button>
      {state === "error" && <span class="err">{err}</span>}
    </div>
  );
}

export function OutcomePanel({ t }: { t: TurnView }) {
  const res = t.outcomeResult;
  const sym = t.classification?.symptomId ?? t.input.symptomId;
  const again = () => void startTurn({ symptomId: sym }, `Tapped: ${symptomLabel(sym)}`);

  if (!res) {
    if (t.status !== "awaiting-outcome") return null;
    return (
      <Card title="After your run" class="outcome outcome-ask">
        <div class="stack">
          <div class="row outcome-row">
            <p class="grow">Run 3 to 5 laps, then tell me how the car felt compared with before.</p>
            <Button variant="ok" size="lg" disabled={busy.value} onClick={() => void sendOutcome("better")}>
              BETTER
            </Button>
            <Button size="lg" disabled={busy.value} onClick={() => void sendOutcome("same")}>
              SAME
            </Button>
            <Button variant="danger" size="lg" disabled={busy.value} onClick={() => void sendOutcome("worse")}>
              WORSE
            </Button>
          </div>
          {actionError.value && <p class="err">{actionError.value}</p>}
        </div>
      </Card>
    );
  }

  const next = res.next?.primary;
  return (
    <Card title={`Outcome: ${t.outcomeChoice}`} class="outcome">
      <div class="stack">
        {res.prompt === "offer-revert" && (
          <Banner
            tone="warn"
            actions={
              !t.reverted && res.revert ? (
                <>
                  <Button variant="warn" size="lg" disabled={busy.value} onClick={() => void revertChange()}>
                    REVERT IT
                  </Button>
                </>
              ) : undefined
            }
          >
            {t.reverted ? (
              <>Reverted. The setup is back to what it was before this change.</>
            ) : (
              <>
                <b>That made it worse.</b> Put it back? Reverting returns <b>{paramLabel(res.revert?.param)}</b> to{" "}
                <b>{String(res.revert?.to ?? "its previous value")}</b> and logs the revert.
              </>
            )}
          </Banner>
        )}
        {res.prompt === "save-setup" && (
          <Banner tone="ok">
            <b>Better.</b> Worth keeping: save this setup with today's track conditions so you can find it on race day.
          </Banner>
        )}
        {res.prompt === "save-setup" && <SaveInline />}
        {res.prompt === "next-lever" && (
          <Banner tone="info">
            <b>No clear change.</b> Try the next option from my notes.
          </Banner>
        )}
        {next && res.prompt !== "save-setup" && (
          <div>
            <div class="card-title">Next in line</div>
            <p>
              <b>{next.lever.action}</b>
              {next.from !== null && next.to !== null && !next.currentOutOfRange && (
                <span class="muted">
                  {" "}
                  {String(next.from)} to {String(next.to)}
                  {next.lever.unit ? ` ${next.lever.unit}` : ""}
                </span>
              )}
            </p>
          </div>
        )}
        {res.next && !res.next.primary && res.next.noLeverReason && <p class="muted">{res.next.noLeverReason}</p>}
        <div class="row">
          {res.prompt !== "save-setup" && sym && (
            <Button variant="primary" onClick={again}>
              Ask the coach again
            </Button>
          )}
          <Button onClick={() => navigate("session")}>Log a run</Button>
          <Button variant="ghost" onClick={resetTurn}>
            Start over
          </Button>
        </div>
        {actionError.value && <p class="err">{actionError.value}</p>}
      </div>
    </Card>
  );
}
