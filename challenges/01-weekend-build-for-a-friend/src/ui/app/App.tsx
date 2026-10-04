// App shell (T4a): left nav + hash router. T0 minimal version so `npm run dev` renders something.
import { useEffect } from "preact/hooks";
import type { ComponentType } from "preact";
import { ROUTES, route, startHashRouter, type Route } from "../store";
import { CoachScreen } from "../coach/CoachScreen";
import { SetupScreen } from "../setup/SetupScreen";
import { SessionScreen } from "../session/SessionScreen";
import { RaceScreen } from "../race/RaceScreen";
import { SettingsScreen } from "../settings/SettingsScreen";

const SCREENS: Record<Route, { label: string; component: ComponentType }> = {
  coach: { label: "Coach", component: CoachScreen },
  setup: { label: "Setup", component: SetupScreen },
  session: { label: "Session", component: SessionScreen },
  race: { label: "Race day", component: RaceScreen },
  settings: { label: "Settings", component: SettingsScreen },
};

export function App() {
  useEffect(() => startHashRouter(), []);
  const Screen = SCREENS[route.value].component;
  return (
    <div class="app">
      <header class="top">
        <h1>RC Pit Companion</h1>
      </header>
      <nav class="tabs" aria-label="Screens">
        {ROUTES.map((r) => (
          <a key={r} href={`#/${r}`} aria-current={route.value === r ? "page" : undefined}>
            {SCREENS[r].label}
          </a>
        ))}
      </nav>
      <main>
        <Screen />
      </main>
    </div>
  );
}
