// Base components (T4a). Import from "../app/components".
//   Button, Chip, Card, Banner, Drawer, CitationChip, citationLabel
// Every Button and Chip is at least 48 px tall (css: --btn-h); `size="lg"` is 64 px for primary actions.
import type { ComponentChildren, JSX } from "preact";
import { useEffect, useRef } from "preact/hooks";
import { openCitation } from "./drawer";

type Tone = "info" | "warn" | "danger" | "ok";

type BtnAttrs = JSX.IntrinsicElements["button"];

export interface ButtonProps extends Omit<BtnAttrs, "size"> {
  variant?: "default" | "primary" | "ok" | "warn" | "danger" | "ghost";
  size?: "md" | "lg";
}

export function Button({ variant = "default", size = "md", class: cls, type = "button", ...rest }: ButtonProps) {
  const c = ["btn", variant !== "default" && `btn-${variant}`, size === "lg" && "btn-lg", cls].filter(Boolean).join(" ");
  return <button type={type} class={c} {...rest} />;
}

export interface ChipProps extends BtnAttrs {
  selected?: boolean;
  tone?: "ok" | "danger";
}

/** Toggle-style chip button (aria-pressed reflects `selected`). */
export function Chip({ selected, tone, class: cls, type = "button", ...rest }: ChipProps) {
  return (
    <button
      type={type}
      class={["chip", cls].filter(Boolean).join(" ")}
      aria-pressed={selected === undefined ? undefined : selected}
      data-tone={tone}
      {...rest}
    />
  );
}

export function Card(props: {
  title?: string;
  tone?: "muted" | "accent";
  class?: string;
  children?: ComponentChildren;
  "aria-label"?: string;
}) {
  return (
    <section class={["card", props.class].filter(Boolean).join(" ")} data-tone={props.tone} aria-label={props["aria-label"]}>
      {props.title && <div class="card-title">{props.title}</div>}
      {props.children}
    </section>
  );
}

export function Banner(props: { tone?: Tone; actions?: ComponentChildren; children?: ComponentChildren; class?: string }) {
  return (
    <div class={["banner", props.class].filter(Boolean).join(" ")} data-tone={props.tone ?? "info"} role={props.tone === "danger" ? "alert" : "status"}>
      <div class="banner-text">{props.children}</div>
      {props.actions && <div class="banner-actions">{props.actions}</div>}
    </div>
  );
}

/** Right-hand drawer. Esc and the scrim close it. */
export function Drawer(props: { open: boolean; title: string; onClose: () => void; children?: ComponentChildren }) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!props.open) return;
    const prev = document.activeElement as HTMLElement | null;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") props.onClose();
    };
    addEventListener("keydown", onKey);
    return () => {
      removeEventListener("keydown", onKey);
      prev?.focus?.();
    };
  }, [props.open]);
  if (!props.open) return null;
  return (
    <>
      <div class="scrim" onClick={props.onClose} />
      <aside class="drawer" role="dialog" aria-modal="true" aria-label={props.title}>
        <div class="drawer-head">
          <h3>{props.title}</h3>
          <button type="button" class="btn" ref={closeRef} onClick={props.onClose} aria-label="Close">
            Close
          </button>
        </div>
        <div class="drawer-body">{props.children}</div>
      </aside>
    </>
  );
}

const PAGE_PREFIX = /^(touring-car-|vehicle-dynamics-|yokomo-)/;

/** "touring-car-suspension-tuning#shock-mounting-angle" -> "suspension tuning: shock mounting angle". */
export function citationLabel(id: string): string {
  const [page, slug = ""] = id.split("#");
  const p = page.replace(PAGE_PREFIX, "").replace(/-/g, " ");
  const s = slug.replace(/-/g, " ");
  const label = s ? `${p}: ${s}` : p;
  return label.length > 44 ? `${label.slice(0, 43)}…` : label;
}

/** A button that opens the global citation drawer with that chunk's text. */
export function CitationChip({ id, label }: { id: string; label?: string }) {
  return (
    <button type="button" class="chip chip-cite" onClick={() => openCitation(id)} title={id}>
      {label ?? citationLabel(id)}
    </button>
  );
}
