// Small controls shared by the settings sections (T4c). Every control is at least 48 px tall and works without hover.
import type { ComponentChildren } from "preact";
import { Chip } from "../app/components";
import "./settings.css";

/** A labelled on/off switch row (role="switch"). */
export function Toggle(props: {
  label: string;
  hint?: ComponentChildren;
  checked: boolean;
  disabled?: boolean;
  onChange: (v: boolean) => void;
  testId?: string;
}) {
  return (
    <div class="st-toggle">
      <div class="st-toggle-text">
        <div class="st-toggle-label" id={`lbl-${props.label.replace(/\W+/g, "-")}`}>
          {props.label}
        </div>
        {props.hint && <div class="muted small">{props.hint}</div>}
      </div>
      <button
        type="button"
        role="switch"
        class="st-switch"
        aria-checked={props.checked}
        aria-labelledby={`lbl-${props.label.replace(/\W+/g, "-")}`}
        data-testid={props.testId}
        disabled={props.disabled}
        onClick={() => props.onChange(!props.checked)}
      >
        <span class="st-switch-state">{props.checked ? "On" : "Off"}</span>
      </button>
    </div>
  );
}

/** Single-choice chip group. */
export function Choice<T extends string>(props: {
  label: string;
  value: T;
  options: { value: T; label: string; title?: string }[];
  onChange: (v: T) => void;
  disabled?: boolean;
}) {
  return (
    <div role="radiogroup" aria-label={props.label} class="row">
      {props.options.map((o) => (
        <Chip
          key={o.value}
          role="radio"
          aria-checked={props.value === o.value}
          selected={props.value === o.value}
          title={o.title}
          disabled={props.disabled}
          onClick={() => props.onChange(o.value)}
        >
          {o.label}
        </Chip>
      ))}
    </div>
  );
}

/** One status row: a coloured dot, a text and an optional detail. */
export function StatusRow(props: { tone: "ok" | "warn" | "danger" | "idle"; children: ComponentChildren }) {
  return (
    <div class="st-status" data-tone={props.tone}>
      <i aria-hidden="true" />
      <span>{props.children}</span>
    </div>
  );
}
