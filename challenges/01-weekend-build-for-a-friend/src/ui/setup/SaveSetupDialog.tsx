// "Save as setup..." dialog (T4b): label, conditions copied from the session, optional verdict.
// Saves the session's current (committed) setup; staged edits are not included, and the dialog says so.
import { useState } from "preact/hooks";
import { request } from "../../api/client";
import type { SavedSetup, Session } from "../../shared/types";
import { Dialog, errorMessage } from "./widgets";

export function conditionsSummary(c: Session["conditions"]): string {
  const parts = [c.trackName || "(no track name)", c.surface, `${c.grip} grip`, c.bumpy ? "bumpy" : "smooth"];
  if (c.layout) parts.push(`${c.layout} layout`);
  if (typeof c.trackTempC === "number") parts.push(`track ${c.trackTempC} C`);
  return parts.join(" | ");
}

export function SaveSetupDialog(props: {
  session: Session;
  /** Latest run in the session, linked to the saved setup when present. */
  latestRunId?: string;
  stagedCount: number;
  onClose: () => void;
  onSaved: (s: SavedSetup) => void;
}) {
  const { session } = props;
  const [label, setLabel] = useState(`${session.conditions.trackName || "Setup"} ${session.date}`);
  const [verdict, setVerdict] = useState("");
  const [eventName, setEventName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function save() {
    if (!label.trim()) {
      setErr("Give the setup a name.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      const saved = await request("POST /api/saved", {
        label: label.trim(),
        setupId: session.currentSetupId,
        conditions: session.conditions,
        sessionId: session.id,
        ...(props.latestRunId ? { runId: props.latestRunId } : {}),
        ...(verdict.trim() ? { verdict: verdict.trim() } : {}),
        ...(eventName.trim() ? { eventName: eventName.trim() } : {}),
      });
      props.onSaved(saved);
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog title="Save as setup" onClose={props.onClose}>
      <label class="pc-field">
        <span class="pc-label">Name</span>
        <input type="text" value={label} onInput={(e) => setLabel((e.target as HTMLInputElement).value)} />
      </label>
      <p class="pc-small">
        <span class="pc-label">Conditions copied from this session: </span>
        {conditionsSummary(session.conditions)}
      </p>
      <label class="pc-field">
        <span class="pc-label">Verdict (optional)</span>
        <input
          type="text"
          placeholder="e.g. good on exits, slightly pushy in the hairpin"
          value={verdict}
          onInput={(e) => setVerdict((e.target as HTMLInputElement).value)}
        />
      </label>
      <label class="pc-field">
        <span class="pc-label">Race or event (optional)</span>
        <input type="text" value={eventName} onInput={(e) => setEventName((e.target as HTMLInputElement).value)} />
      </label>
      {props.stagedCount > 0 && (
        <p class="pc-flag">
          {props.stagedCount} staged change{props.stagedCount > 1 ? "s are" : " is"} not committed and will not be saved.
          Commit first to include {props.stagedCount > 1 ? "them" : "it"}.
        </p>
      )}
      {err && <p class="pc-err" role="alert">{err}</p>}
      <div class="pc-row">
        <button type="button" class="pc-btn primary" disabled={busy} onClick={save}>
          {busy ? "Saving..." : "Save setup"}
        </button>
        <button type="button" class="pc-btn" onClick={props.onClose}>
          Cancel
        </button>
      </div>
    </Dialog>
  );
}
