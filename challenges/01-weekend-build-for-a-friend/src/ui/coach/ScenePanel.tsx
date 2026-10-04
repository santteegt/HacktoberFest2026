// 3D/2D explainer slot (plan section 6). Uses only the CarScene interface from src/scene; the T0 no-op scene
// (explainerFor returns null) means the panel simply does not render until T5 lands.
import { useEffect, useRef } from "preact/hooks";
import { createCarScene, explainerFor, type CarScene, type SceneBinding, type SceneView } from "../../scene";
import { Button, Card } from "../app/components";
import { meta } from "../store";

const VIEWS: { v: SceneView; label: string }[] = [
  { v: "auto", label: "Auto" },
  { v: "front", label: "Front" },
  { v: "side", label: "Side" },
  { v: "top", label: "Top" },
  { v: "iso", label: "Iso" },
];

export function ScenePanel({ binding }: { binding: SceneBinding }) {
  const host = useRef<HTMLDivElement>(null);
  const scene = useRef<CarScene | null>(null);
  const available = explainerFor(binding.param) !== null;

  useEffect(() => {
    if (!available || !host.current) return;
    const s = createCarScene();
    s.mount(host.current);
    scene.current = s;
    return () => {
      s.dispose();
      scene.current = null;
    };
  }, [available]);

  useEffect(() => {
    if (!available) return;
    scene.current?.setView("auto");
    scene.current?.showChange(binding);
  }, [available, binding.explainer, binding.param, binding.from, binding.to]);

  if (!available) return null;
  return (
    <Card title={`Where it moves: ${meta.value?.params.find((p) => p.id === binding.param)?.label.replace(/\s*\(.*$/, "") ?? binding.param}`} class="scene-card">
      <div ref={host} class="scene-host" role="img" aria-label={`Schematic of ${binding.explainer}, from ${binding.from} to ${binding.to}`} />
      <p class="muted small">Ghost = now, solid = after.</p>
      <div class="row">
        {VIEWS.map((x) => (
          <Button key={x.v} onClick={() => scene.current?.setView(x.v)}>
            {x.label}
          </Button>
        ))}
      </div>
    </Card>
  );
}
