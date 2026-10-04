// Small local components shared by the Setup and Session screens (T4b owns them; T4a's shared set is not required).
import type { ComponentChildren } from "preact";
import "./widgets.css";

export interface ChipOption<T extends string> {
  value: T;
  label: string;
  title?: string;
}

/** Single-select chip group (radio semantics). Tapping the selected chip clears it when `clearable`. */
export function ChipSelect<T extends string>(props: {
  label: string;
  options: ChipOption<T>[];
  value: T | undefined;
  onChange: (v: T | undefined) => void;
  clearable?: boolean;
}) {
  return (
    <div role="radiogroup" aria-label={props.label} class="pc-chips">
      {props.options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          class="pc-chip"
          aria-checked={props.value === o.value}
          title={o.title}
          onClick={() => props.onChange(props.value === o.value && props.clearable ? undefined : o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Multi-select chip group (toggle buttons). */
export function ChipMulti(props: {
  label: string;
  options: ChipOption<string>[];
  value: string[];
  onChange: (v: string[]) => void;
}) {
  return (
    <div role="group" aria-label={props.label} class="pc-chips">
      {props.options.map((o) => {
        const on = props.value.includes(o.value);
        return (
          <button
            key={o.value}
            type="button"
            class="pc-chip"
            aria-pressed={on}
            title={o.title}
            onClick={() => props.onChange(on ? props.value.filter((x) => x !== o.value) : [...props.value, o.value])}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

export function Dialog(props: { title: string; onClose: () => void; children: ComponentChildren }) {
  return (
    <div class="pc-overlay" onClick={(e) => e.target === e.currentTarget && props.onClose()}>
      <div class="pc-dialog" role="dialog" aria-modal="true" aria-label={props.title}>
        <h3>{props.title}</h3>
        {props.children}
      </div>
    </div>
  );
}

export function errorMessage(e: unknown): string {
  if (e && typeof e === "object" && "error" in e && typeof (e as { error: unknown }).error === "string") {
    return (e as { error: string }).error;
  }
  return e instanceof Error ? e.message : String(e);
}
