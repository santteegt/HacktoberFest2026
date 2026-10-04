// First-run overlay (T4a, plan 5.5): 1) car profile, 2) start a session, 3) model check.
import { useState } from "preact/hooks";
import { createSession, putSettings } from "../../api/client";
import type { CarId, Grip, TrackConditions } from "../../shared/types";
import { llmStatus, settings } from "../store";
import { firstRun, markFirstRunDone, pollLlmStatus, setActiveSession } from "./bootstrap";
import { modelShortName } from "./StatusBar";
import { Banner, Button, Chip } from "./components";

const SURFACES: TrackConditions["surface"][] = ["asphalt", "carpet", "concrete", "other"];
const GRIPS: Grip[] = ["low", "medium", "high"];

export function FirstRun() {
  const { open, step } = firstRun.value;
  const [car, setCar] = useState<CarId>(settings.value?.car ?? "yokomo-bd12");
  const [track, setTrack] = useState("");
  const [surface, setSurface] = useState<TrackConditions["surface"]>("asphalt");
  const [grip, setGrip] = useState<Grip>("medium");
  const [bumpy, setBumpy] = useState(false);
  const [temp, setTemp] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  if (!open) return null;
  const go = (s: 1 | 2 | 3) => (firstRun.value = { open: true, step: s });

  async function pickCar() {
    setBusy(true);
    setErr(null);
    try {
      settings.value = await putSettings({ car });
      go(2);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function start() {
    setBusy(true);
    setErr(null);
    try {
      const conditions: TrackConditions = { trackName: track.trim() || "Practice", surface, grip, bumpy };
      const t = Number(temp);
      if (temp.trim() && Number.isFinite(t)) conditions.trackTempC = settings.value?.tempUnit === "F" ? Math.round(((t - 32) * 5) / 9) : t;
      const s = await createSession({ date: new Date().toISOString().slice(0, 10), car: settings.value?.car ?? car, conditions });
      await setActiveSession(s.id);
      void pollLlmStatus();
      go(3);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const st = llmStatus.value;
  const model = st?.model ?? settings.value?.model ?? "gemma4:e2b-it-qat";
  return (
    <div class="overlay" role="dialog" aria-modal="true" aria-label="First run setup">
      <div class="modal">
        <div class="steps" aria-hidden="true">
          {[1, 2, 3].map((n) => (
            <i key={n} data-on={n <= step} />
          ))}
        </div>

        {step === 1 && (
          <>
            <div>
              <h2>Welcome to the pit</h2>
              <p class="muted">Step 1 of 3: which car are we tuning?</p>
            </div>
            <div class="row">
              <Chip selected={car === "yokomo-bd12"} onClick={() => setCar("yokomo-bd12")}>
                Yokomo BD12
              </Chip>
              <Chip selected={car === "generic"} onClick={() => setCar("generic")}>
                Generic 1/10 touring car
              </Chip>
            </div>
            <p class="muted small">BD12 starts from Yokomo's factory values; anything Yokomo does not give falls back to a generic value, tagged as generic.</p>
            {err && <Banner tone="danger">{err}</Banner>}
            <div class="row">
              <Button variant="primary" size="lg" disabled={busy} onClick={pickCar}>
                Next
              </Button>
              <Button variant="ghost" onClick={markFirstRunDone}>
                Skip setup
              </Button>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <div>
              <h2>Start a practice session</h2>
              <p class="muted">Step 2 of 3: where are you running today? Change it any time.</p>
            </div>
            <div>
              <label class="label" for="fr-track">Track name</label>
              <input id="fr-track" class="field" value={track} onInput={(e) => setTrack((e.target as HTMLInputElement).value)} placeholder="Club track" />
            </div>
            <div>
              <span class="label">Surface</span>
              <div class="row">
                {SURFACES.map((s) => (
                  <Chip key={s} selected={surface === s} onClick={() => setSurface(s)}>
                    {s}
                  </Chip>
                ))}
              </div>
            </div>
            <div>
              <span class="label">Grip</span>
              <div class="row">
                {GRIPS.map((g) => (
                  <Chip key={g} selected={grip === g} onClick={() => setGrip(g)}>
                    {g}
                  </Chip>
                ))}
                <Chip selected={bumpy} onClick={() => setBumpy(!bumpy)}>
                  bumpy
                </Chip>
              </div>
            </div>
            <div>
              <label class="label" for="fr-temp">Track temperature ({settings.value?.tempUnit ?? "C"}, optional)</label>
              <input id="fr-temp" class="field" inputMode="decimal" value={temp} onInput={(e) => setTemp((e.target as HTMLInputElement).value)} style="max-width:180px" />
            </div>
            {err && <Banner tone="danger">{err}</Banner>}
            <div class="row">
              <Button variant="primary" size="lg" disabled={busy} onClick={start}>
                Start session
              </Button>
              <Button variant="ghost" onClick={markFirstRunDone}>
                Not now
              </Button>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <div>
              <h2>Check the coach model</h2>
              <p class="muted">Step 3 of 3: the coach phrases its advice with a local model. The tap chips and the setup vault work without it.</p>
            </div>
            {!st ? (
              <Banner tone="info" actions={<Button onClick={() => void pollLlmStatus()}>Check again</Button>}>
                Checking Ollama…
              </Banner>
            ) : !st.reachable ? (
              <Banner tone="warn" actions={<Button onClick={() => void pollLlmStatus()}>Check again</Button>}>
                Ollama is not reachable at <code>{st.url}</code>. Start the Ollama app, or continue with chips only.
              </Banner>
            ) : !st.present ? (
              <Banner tone="warn" actions={<Button onClick={() => void pollLlmStatus()}>Check again</Button>}>
                Ollama is running but <code>{model}</code> is not pulled. In a terminal run <code>ollama pull gemma4:e2b-it-qat</code>, or pull it from Settings.
              </Banner>
            ) : (
              <Banner tone="ok">
                {modelShortName(st.model)} is ready{st.loaded ? "." : " (it loads on first use, so the first answer is slower)."}
              </Banner>
            )}
            <div class="row">
              <Button variant="primary" size="lg" onClick={markFirstRunDone}>
                {st?.reachable && st.present ? "Start coaching" : "Skip, use chips only"}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
