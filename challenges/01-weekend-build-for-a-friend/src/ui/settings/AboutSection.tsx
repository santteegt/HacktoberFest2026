// Settings > About (T4c): provenance summary with the text of kb/PROVENANCE.md, version, offline checklist.
// The checklist shows what the app can see. It does not prove the app works with Wi-Fi off.
import { useEffect, useState } from "preact/hooks";
import { getHealth } from "../../api/client";
import provenanceText from "../../../kb/PROVENANCE.md?raw";
import { Button, Card, Drawer } from "../app/components";
import { pollLlmStatus } from "../app/bootstrap";
import { llmStatus, meta, settings } from "../store";
import { localProbe, localVoices, refreshLocalProbe, refreshVoices } from "./state";
import { StatusRow } from "./ui";

export function AboutSection() {
  const [version, setVersion] = useState<string | null>(null);
  const [showProv, setShowProv] = useState(false);
  const s = settings.value;
  const st = llmStatus.value;
  const probe = localProbe.value;
  const voices = localVoices.value;
  const kb = meta.value?.kbStats;

  useEffect(() => {
    getHealth()
      .then((h) => setVersion(h.version))
      .catch(() => setVersion(null));
    void pollLlmStatus();
    void refreshLocalProbe();
    void refreshVoices();
  }, []);

  const modelOk = !!st?.present;
  const packOk = !!probe?.onDeviceReady;
  let voiceOk = false;
  let voiceText = "No local voice selected (voice output is off).";
  if (s?.voiceOut === "say") {
    voiceOk = true;
    voiceText = "macOS say is selected (a local voice).";
  } else if (s?.voiceOut === "browser") {
    const named = !!s.voiceName && (voices ?? []).some((v) => v.name === s.voiceName);
    voiceOk = named;
    voiceText = named ? `Local browser voice selected: ${s.voiceName}.` : "Browser output is on but no specific local voice is picked: choose one under Voice.";
  }

  return (
    <Card title="About" class="st-card st-wide" aria-label="About">
      <p>
        <b>RC Pit Companion</b>
        {version ? ` version ${version}` : ""}. The app code was written inside the Hacktoberfest 2026 Weekend Challenge window. The setup knowledge it quotes comes from the author's own touring-car notes, written before the window, imported as a frozen, hash-checked snapshot and credited.
        {kb ? ` Compiled for the coach: ${kb.pages} pages, ${kb.chunks} chunks (content hash ${kb.contentHash.slice(0, 12)}).` : ""}
      </p>
      <div class="st-actions">
        <Button onClick={() => setShowProv(true)} data-testid="open-provenance">Read kb/PROVENANCE.md</Button>
      </div>

      <h3>Offline checklist</h3>
      <ul class="st-check" data-testid="offline-checklist">
        <li>
          <StatusRow tone={modelOk ? "ok" : "danger"}>{modelOk ? `Model present: ${st?.model}.` : st ? `Model not pulled: ${st.model}.` : "Model status unknown (server not answering)."}</StatusRow>
        </li>
        <li>
          <StatusRow tone={packOk ? "ok" : "warn"}>{packOk ? "On-device speech pack reported installed." : probe ? `Speech pack: ${probe.detail}` : "Speech pack status not checked yet."}</StatusRow>
        </li>
        <li>
          <StatusRow tone={voiceOk ? "ok" : "warn"}>{voiceText}</StatusRow>
        </li>
      </ul>
      <p class="st-note" data-tone="warn">
        These ticks show what the app can see on this machine. They do not prove anything works offline: test with Wi-Fi off.
      </p>

      <Drawer open={showProv} title="kb/PROVENANCE.md" onClose={() => setShowProv(false)}>
        <pre class="st-pre">{provenanceText}</pre>
      </Drawer>
    </Card>
  );
}
