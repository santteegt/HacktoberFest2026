// Settings > Car and units (T4c).
import { useState } from "preact/hooks";
import type { Settings } from "../../shared/types";
import { Card } from "../app/components";
import { errText, saveSettings } from "./state";
import { Choice } from "./ui";

export function CarSection({ s }: { s: Settings }) {
  const [err, setErr] = useState<string | null>(null);
  const fail = (e: unknown) => setErr(errText(e));
  return (
    <Card title="Car and units" class="st-card" aria-label="Car and units">
      <div class="st-field">
        <span class="label">Car profile</span>
        <Choice<Settings["car"]>
          label="Car profile"
          value={s.car}
          options={[
            { value: "yokomo-bd12", label: "Yokomo BD12" },
            { value: "generic", label: "Generic touring car" },
          ]}
          onChange={(v) => void saveSettings({ car: v }).catch(fail)}
        />
        <span class="muted small">Used for new sessions; sessions already logged keep the car they were started with.</span>
      </div>
      <div class="st-field">
        <span class="label">Temperature</span>
        <Choice<Settings["tempUnit"]>
          label="Temperature unit"
          value={s.tempUnit}
          options={[
            { value: "C", label: "Celsius (C)" },
            { value: "F", label: "Fahrenheit (F)" },
          ]}
          onChange={(v) => void saveSettings({ tempUnit: v }).catch(fail)}
        />
        <span class="muted small">Applies to the top bar and the first-run form. The condition forms still take Celsius.</span>
      </div>
      {err && <p class="st-err" role="alert">{err}</p>}
    </Card>
  );
}
