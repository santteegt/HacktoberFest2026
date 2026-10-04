// Settings > Voice (T4c). Shows the live speech status from src/voice and never states that offline voice works:
// it has to be tested with Wi-Fi off on the machine that will use it.
import { useEffect, useMemo, useRef, useState } from "preact/hooks";
import type { Settings } from "../../shared/types";
import { createSpeechInput, createSpeechOutput, installSpeechPack } from "../../voice";
import type { SpeechInput } from "../../voice";
import { Button, Card } from "../app/components";
import { errText, localVoices, refreshLocalProbe, refreshSpeechStatus, refreshVoices, saveSettings, speechStatus } from "./state";
import { Choice, StatusRow } from "./ui";

const TEST_PHRASE = "Check one. The rear shocks are one hole more upright. Try three to five laps.";

export function VoiceSection({ s }: { s: Settings }) {
  const [err, setErr] = useState<string | null>(null);
  const [installing, setInstalling] = useState(false);
  const [installMsg, setInstallMsg] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [testMsg, setTestMsg] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const [heard, setHeard] = useState<string | null>(null);
  const mic = useRef<SpeechInput | null>(null);
  const status = speechStatus.value;
  const voices = localVoices.value;

  useEffect(() => {
    void refreshSpeechStatus(s.voiceIn);
  }, [s.voiceIn]);
  useEffect(() => {
    void refreshVoices();
    void refreshLocalProbe();
  }, []);

  const micLabel = useMemo(() => {
    try {
      return createSpeechInput(s).label ?? null;
    } catch {
      return null;
    }
  }, [s.voiceIn]);

  const fail = (e: unknown) => setErr(errText(e));

  async function install() {
    setInstalling(true);
    setInstallMsg(null);
    try {
      const ok = await installSpeechPack();
      setInstallMsg(ok ? "Speech pack installed." : "The install did not finish. It needs desktop Chrome 139 or newer and the internet once.");
    } finally {
      setInstalling(false);
      void refreshSpeechStatus(s.voiceIn);
      void refreshLocalProbe();
    }
  }

  async function testInput() {
    setHeard(null);
    setListening(true);
    try {
      const input = createSpeechInput(s);
      mic.current = input;
      input.onInterim = (t) => setHeard(`${t} ...`);
      const text = await input.listen();
      setHeard(text ? `Heard: "${text}"` : "Heard nothing.");
    } catch (e) {
      setHeard(`Voice input test failed: ${errText(e)}`);
    } finally {
      setListening(false);
      mic.current = null;
    }
  }

  async function test() {
    setTesting(true);
    setTestMsg(null);
    try {
      await createSpeechOutput(s).speak(TEST_PHRASE);
      setTestMsg("Test finished. If you heard nothing, pick another voice or output.");
    } catch (e) {
      setTestMsg(`Test failed: ${errText(e)}`);
    } finally {
      setTesting(false);
    }
  }

  function stopTest() {
    try {
      createSpeechOutput(s).cancel();
    } catch {
      /* nothing playing */
    }
  }

  const tone = !status ? "idle" : status.state === "available" ? "ok" : status.state === "cloud" ? "warn" : status.state === "off" ? "idle" : status.state === "downloadable" || status.state === "downloading" ? "warn" : "danger";
  const english = (voices ?? []).filter((v) => /^en([-_]|$)/i.test(v.lang));
  const others = (voices ?? []).filter((v) => !/^en([-_]|$)/i.test(v.lang));
  const voiceKnown = !s.voiceName || (voices ?? []).some((v) => v.name === s.voiceName);

  return (
    <Card title="Voice" class="st-card" aria-label="Voice settings">
      <div class="st-field">
        <span class="label">Voice input</span>
        <Choice<Settings["voiceIn"]>
          label="Voice input"
          value={s.voiceIn}
          options={[
            { value: "local", label: "On this computer (Chrome on-device)" },
            { value: "cloud-optin", label: "Chrome online (audio goes to Google)", title: "Opt in only: the browser sends your audio to Google for recognition." },
            { value: "off", label: "Off" },
          ]}
          onChange={(v) => void saveSettings({ voiceIn: v }).catch(fail)}
        />
        <div aria-live="polite" data-testid="speech-status">
          <StatusRow tone={tone}>{status ? status.detail : "Checking the browser..."}</StatusRow>
        </div>
        {micLabel && <span class="muted small">Mic label in the coach: {micLabel}</span>}
        <div class="st-actions">
          <Button disabled={installing || s.voiceIn !== "local" || status?.state === "available"} onClick={() => void install()}>
            {installing ? "Installing..." : "Install speech pack"}
          </Button>
          {installMsg && <span class="muted small">{installMsg}</span>}
        </div>
        <div class="st-actions">
          <Button disabled={s.voiceIn === "off" || listening} onClick={() => void testInput()} data-testid="test-mic">
            {listening ? "Listening..." : "Test voice input"}
          </Button>
          {listening && <Button variant="ghost" onClick={() => mic.current?.stop?.()}>Stop listening</Button>}
          {heard && <span class="muted small" data-testid="heard">{heard}</span>}
        </div>
        <p class="st-note" data-tone="warn">
          Unverified on this machine until you test with Wi-Fi off. The status line above only reports what the browser says.
        </p>
      </div>

      <div class="st-field">
        <span class="label">Voice output</span>
        <Choice<Settings["voiceOut"]>
          label="Voice output"
          value={s.voiceOut}
          options={[
            { value: "browser", label: "Browser local voice" },
            { value: "say", label: "macOS say" },
            { value: "off", label: "Off" },
          ]}
          onChange={(v) => void saveSettings({ voiceOut: v }).catch(fail)}
        />
        {s.voiceOut === "browser" && (
          <div class="st-field">
            <label class="label" for="st-voice">Voice (local voices only)</label>
            <select
              id="st-voice"
              class="st-select"
              value={s.voiceName ?? ""}
              onChange={(e) => void saveSettings({ voiceName: (e.target as HTMLSelectElement).value }).catch(fail)}
            >
              <option value="">Browser default</option>
              <optgroup label="English">
                {english.map((v) => (
                  <option key={`${v.name}|${v.lang}`} value={v.name}>
                    {v.name} ({v.lang}){v.default ? " default" : ""}
                  </option>
                ))}
              </optgroup>
              {others.length > 0 && (
                <optgroup label="Other languages (the coach speaks English)">
                  {others.map((v) => (
                    <option key={`${v.name}|${v.lang}`} value={v.name}>
                      {v.name} ({v.lang})
                    </option>
                  ))}
                </optgroup>
              )}
              {!voiceKnown && s.voiceName && <option value={s.voiceName}>{s.voiceName} (not in this browser's list)</option>}
            </select>
            {voices && voices.length === 0 && <span class="muted small">This browser lists no local voices. Try macOS say.</span>}
          </div>
        )}
        {s.voiceOut === "say" && (
          <div class="st-field">
            <label class="label" for="st-sayvoice">macOS voice name (optional, e.g. Samantha)</label>
            <input
              id="st-sayvoice"
              class="field"
              type="text"
              defaultValue={s.voiceName ?? ""}
              onBlur={(e) => {
                const v = (e.target as HTMLInputElement).value.trim();
                if (v !== (s.voiceName ?? "")) void saveSettings({ voiceName: v }).catch(fail);
              }}
            />
          </div>
        )}
        <div class="st-actions">
          <Button disabled={s.voiceOut === "off" || testing} onClick={() => void test()} data-testid="test-voice">
            {testing ? "Speaking..." : "Test voice"}
          </Button>
          {testing && <Button variant="ghost" onClick={stopTest}>Stop</Button>}
          {testMsg && <span class="muted small">{testMsg}</span>}
        </div>
      </div>
      {err && <p class="st-err" role="alert">{err}</p>}
    </Card>
  );
}
