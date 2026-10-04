// Settings screen (T4c, plan 5.5): Model, Advice, Voice, Car and units, Data, About. Changes persist through PUT /api/settings.
import { settings } from "../store";
import { AboutSection } from "./AboutSection";
import { AdviceSection } from "./AdviceSection";
import { CarSection } from "./CarSection";
import { DataSection } from "./DataSection";
import { ModelSection } from "./ModelSection";
import { VoiceSection } from "./VoiceSection";
import "./settings.css";

export function SettingsScreen() {
  const s = settings.value;
  return (
    <section class="screen" aria-labelledby="settings-title">
      <h2 id="settings-title">Settings</h2>
      {!s ? (
        <p class="muted" style="margin-top:12px">Loading settings...</p>
      ) : (
        <div class="st-grid">
          <ModelSection s={s} />
          <div class="stack">
            <AdviceSection s={s} />
            <CarSection s={s} />
          </div>
          <div class="st-wide">
            <VoiceSection s={s} />
          </div>
          <DataSection />
          <AboutSection />
        </div>
      )}
    </section>
  );
}
