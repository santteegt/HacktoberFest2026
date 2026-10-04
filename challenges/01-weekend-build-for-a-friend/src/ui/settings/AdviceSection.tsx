// Settings > Advice (T4c): "reviewed lever rows only" with the reviewed / draft counts from meta.levers.
import { useState } from "preact/hooks";
import type { Settings } from "../../shared/types";
import { Card } from "../app/components";
import { meta } from "../store";
import { errText, saveSettings } from "./state";
import { Toggle } from "./ui";

export function AdviceSection({ s }: { s: Settings }) {
  const [err, setErr] = useState<string | null>(null);
  const levers = meta.value?.levers ?? [];
  const reviewed = levers.filter((l) => l.status === "reviewed").length;
  const draft = levers.filter((l) => l.status !== "reviewed").length;
  return (
    <Card title="Advice" class="st-card" aria-label="Advice settings">
      <div class="st-counts" data-testid="lever-counts">
        <div class="st-count">
          <b>{reviewed}</b>
          <span>reviewed lever rows</span>
        </div>
        <div class="st-count">
          <b>{draft}</b>
          <span>draft lever rows (not yet reviewed)</span>
        </div>
      </div>
      <Toggle
        label="Use reviewed lever rows only"
        hint={
          s.reviewedOnly
            ? "On: the coach skips draft rows, so it may find nothing to suggest for some symptoms."
            : "Off: the coach may suggest from draft rows, and the card says when a row is a draft."
        }
        checked={s.reviewedOnly}
        testId="toggle-reviewedOnly"
        onChange={(v) => void saveSettings({ reviewedOnly: v }).catch((e) => setErr(errText(e)))}
      />
      {err && <p class="st-err" role="alert">{err}</p>}
    </Card>
  );
}
