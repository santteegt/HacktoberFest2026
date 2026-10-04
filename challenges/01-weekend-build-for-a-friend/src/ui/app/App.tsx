// App shell (T4a): status bar, left nav, hash router, citation drawer host, first-run overlay.
import { useEffect } from "preact/hooks";
import type { ComponentType } from "preact";
import { ROUTES, route, startHashRouter, type Route } from "../store";
import { CoachScreen } from "../coach/CoachScreen";
import { SetupScreen } from "../setup/SetupScreen";
import { SessionScreen } from "../session/SessionScreen";
import { RaceScreen } from "../race/RaceScreen";
import { SettingsScreen } from "../settings/SettingsScreen";
import { bootError, bootstrap, bootState } from "./bootstrap";
import { Banner, Button } from "./components";
import { DrawerHost } from "./DrawerHost";
import { FirstRun } from "./FirstRun";
import { StatusBar } from "./StatusBar";

const SCREENS: Record<Route, { label: string; component: ComponentType }> = {
  coach: { label: "Coach", component: CoachScreen },
  setup: { label: "Setup", component: SetupScreen },
  session: { label: "Session", component: SessionScreen },
  race: { label: "Race day", component: RaceScreen },
  settings: { label: "Settings", component: SettingsScreen },
};

export function App() {
  useEffect(() => startHashRouter(), []);
  useEffect(() => {
    void bootstrap();
  }, []);
  const Screen = SCREENS[route.value].component;
  return (
    <div class="shell">
      <StatusBar />
      <div class="body">
        <nav class="nav" aria-label="Screens">
          {ROUTES.map((r) => (
            <a key={r} href={`#/${r}`} aria-current={route.value === r ? "page" : undefined}>
              {SCREENS[r].label}
            </a>
          ))}
        </nav>
        <main class="main">
          {bootState.value === "error" && (
            <Banner
              tone="warn"
              class="boot-banner"
              actions={<Button onClick={() => void bootstrap()}>Try again</Button>}
            >
              The pit server did not answer ({bootError.value}). Is <code>npm run dev</code> running? Tap chips still work once it is.
            </Banner>
          )}
          <Screen />
        </main>
      </div>
      <DrawerHost />
      <FirstRun />
    </div>
  );
}
