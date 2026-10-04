// "Thinking" step list with live timers (plan 5.1/5.5): Understanding -> Picking a change -> Phrasing, plus Cancel.
import { useEffect, useState } from "preact/hooks";
import { llmStatus } from "../store";
import { Button } from "../app/components";
import { cancelTurn, type TurnView } from "./state";

const fmt = (ms: number) => (ms < 50 ? "instant" : `${(ms / 1000).toFixed(1)} s`);

export function Thinking({ t }: { t: TurnView }) {
  const [, setTick] = useState(0);
  useEffect(() => {
    const i = setInterval(() => setTick((n) => n + 1), 100);
    return () => clearInterval(i);
  }, []);
  const now = performance.now();
  const { start, classified, suggestion, explained } = t.t;
  const chip = t.classification?.source === "chip" || (!!t.input.symptomId && !t.input.utterance);

  const steps: { label: string; state: "wait" | "run" | "done"; time: string }[] = [
    {
      label: chip ? "Reading your tap" : "Understanding what you said",
      state: classified ? "done" : "run",
      time: classified ? fmt(t.classification?.ms ?? classified - start) : fmt(now - start),
    },
    {
      label: "Picking a change",
      state: suggestion ? "done" : classified ? "run" : "wait",
      time: suggestion ? fmt(suggestion - (classified ?? start)) : classified ? fmt(now - classified) : "",
    },
    {
      label: "Phrasing",
      state: explained ? "done" : suggestion ? "run" : "wait",
      time: explained ? fmt(t.explanation?.ms ?? explained - (suggestion ?? start)) : suggestion ? fmt(now - suggestion) : "",
    },
  ];
  const slow = llmStatus.value && llmStatus.value.reachable && !llmStatus.value.loaded && now - start > 1500;
  return (
    <section class="thinking-bar" aria-label="Coach progress">
      <span class="card-title thinking-title">Working on it</span>
      <ol class="steps-list">
        {steps.map((s) => (
          <li key={s.label} data-state={s.state}>
            <span class="dot" aria-hidden="true" />
            <span>{s.label}</span>
            <span class="muted time">{s.time}</span>
          </li>
        ))}
      </ol>
      <Button onClick={cancelTurn}>Cancel</Button>
      {slow && <p class="muted small thinking-note">First answer after start can take longer while the model loads.</p>}
    </section>
  );
}
