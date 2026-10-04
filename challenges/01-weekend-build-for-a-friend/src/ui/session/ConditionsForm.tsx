// Track conditions form used to start a session and to edit its conditions (T4b). About five taps for a repeat track.
import { useState } from "preact/hooks";
import type { Grip, Session, TrackConditions } from "../../shared/types";
import { ChipSelect, errorMessage } from "../setup/widgets";

type Surface = TrackConditions["surface"];
type Layout = NonNullable<TrackConditions["layout"]>;

export const EMPTY_CONDITIONS: TrackConditions = { trackName: "", surface: "asphalt", grip: "medium", bumpy: false };

export function ConditionsForm(props: {
  initial?: TrackConditions;
  submitLabel: string;
  /** Past sessions: autocomplete track names and prefill the chips when a known track is typed. */
  past?: Session[];
  onSubmit: (c: TrackConditions) => Promise<void>;
  onCancel?: () => void;
}) {
  const init = props.initial ?? EMPTY_CONDITIONS;
  const [name, setName] = useState(init.trackName);
  const [surface, setSurface] = useState<Surface>(init.surface);
  const [grip, setGrip] = useState<Grip>(init.grip);
  const [bumpy, setBumpy] = useState(init.bumpy);
  const [layout, setLayout] = useState<Layout | undefined>(init.layout);
  const [temp, setTemp] = useState(typeof init.trackTempC === "number" ? String(init.trackTempC) : "");
  const [touched, setTouched] = useState(Boolean(props.initial));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const trackNames = [...new Set((props.past ?? []).map((s) => s.conditions.trackName).filter(Boolean))];

  function onName(v: string) {
    setName(v);
    if (touched) return;
    const hit = [...(props.past ?? [])].reverse().find((s) => s.conditions.trackName.toLowerCase() === v.trim().toLowerCase());
    if (hit) {
      setSurface(hit.conditions.surface);
      setGrip(hit.conditions.grip);
      setBumpy(hit.conditions.bumpy);
      setLayout(hit.conditions.layout);
    }
  }

  async function submit(e: Event) {
    e.preventDefault();
    if (!name.trim()) {
      setErr("Enter the track name.");
      return;
    }
    const t = temp.trim().replace(",", ".");
    const trackTempC = t === "" ? undefined : Number(t);
    if (trackTempC !== undefined && !Number.isFinite(trackTempC)) {
      setErr("Track temperature must be a number.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await props.onSubmit({
        ...(props.initial ?? {}),
        trackName: name.trim(),
        surface,
        grip,
        bumpy,
        ...(layout ? { layout } : { layout: undefined }),
        ...(trackTempC !== undefined ? { trackTempC } : { trackTempC: undefined }),
      });
    } catch (e2) {
      setErr(errorMessage(e2));
    } finally {
      setBusy(false);
    }
  }

  const mark = () => setTouched(true);

  return (
    <form onSubmit={submit}>
      <label class="pc-field">
        <span class="pc-label">Track name</span>
        <input
          type="text"
          list="se-track-names"
          autoComplete="off"
          value={name}
          onInput={(e) => onName((e.target as HTMLInputElement).value)}
        />
        <datalist id="se-track-names">
          {trackNames.map((n) => (
            <option key={n} value={n} />
          ))}
        </datalist>
      </label>
      <div class="pc-field">
        <span class="pc-label">Surface</span>
        <ChipSelect<Surface>
          label="Surface"
          value={surface}
          onChange={(v) => {
            mark();
            if (v) setSurface(v);
          }}
          options={[
            { value: "asphalt", label: "Asphalt" },
            { value: "carpet", label: "Carpet" },
            { value: "concrete", label: "Concrete" },
            { value: "other", label: "Other" },
          ]}
        />
      </div>
      <div class="pc-field">
        <span class="pc-label">Grip today</span>
        <ChipSelect<Grip>
          label="Grip"
          value={grip}
          onChange={(v) => {
            mark();
            if (v) setGrip(v);
          }}
          options={[
            { value: "low", label: "Low" },
            { value: "medium", label: "Medium" },
            { value: "high", label: "High" },
          ]}
        />
      </div>
      <div class="pc-field">
        <span class="pc-label">Surface feel</span>
        <ChipSelect<"smooth" | "bumpy">
          label="Bumpy"
          value={bumpy ? "bumpy" : "smooth"}
          onChange={(v) => {
            mark();
            if (v) setBumpy(v === "bumpy");
          }}
          options={[
            { value: "smooth", label: "Smooth" },
            { value: "bumpy", label: "Bumpy" },
          ]}
        />
      </div>
      <div class="pc-field">
        <span class="pc-label">Layout (optional)</span>
        <ChipSelect<Layout>
          label="Layout"
          value={layout}
          clearable
          onChange={(v) => {
            mark();
            setLayout(v);
          }}
          options={[
            { value: "tight", label: "Tight" },
            { value: "medium", label: "Medium" },
            { value: "fast", label: "Fast" },
          ]}
        />
      </div>
      <label class="pc-field" style="max-width:240px">
        <span class="pc-label">Track temperature, C (optional)</span>
        <input type="text" inputMode="decimal" value={temp} onInput={(e) => setTemp((e.target as HTMLInputElement).value)} />
      </label>
      {err && (
        <p class="pc-err" role="alert">
          {err}
        </p>
      )}
      <div class="pc-row">
        <button type="submit" class="pc-btn primary" disabled={busy}>
          {busy ? "Working..." : props.submitLabel}
        </button>
        {props.onCancel && (
          <button type="button" class="pc-btn" onClick={props.onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
