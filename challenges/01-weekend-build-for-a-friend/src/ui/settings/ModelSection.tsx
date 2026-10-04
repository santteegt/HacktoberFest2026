// Settings > Model (T4c): Ollama URL, model name, live status, pull with a progress bar (SSE), warm up, phrasing toggle.
import { useEffect, useRef, useState } from "preact/hooks";
import { pullModel, warmupLlm } from "../../api/client";
import type { Settings } from "../../shared/types";
import { Button, Card } from "../app/components";
import { pollLlmStatus } from "../app/bootstrap";
import { llmStatus } from "../store";
import { errText, saveSettings } from "./state";
import { StatusRow, Toggle } from "./ui";

const SUGGESTED = ["gemma4:e2b-it-qat", "gemma4:e4b-it-qat"];

interface Pull {
  status: string;
  completed?: number;
  total?: number;
}

const gb = (n: number) => `${(n / 1e9).toFixed(2)} GB`;

export function ModelSection({ s }: { s: Settings }) {
  const [url, setUrl] = useState(s.ollamaUrl);
  const [model, setModel] = useState(s.model);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ tone: "ok" | "err"; text: string } | null>(null);
  const [pull, setPull] = useState<Pull | null>(null);
  const [pulling, setPulling] = useState(false);
  const [warm, setWarm] = useState<string | null>(null);
  const [warming, setWarming] = useState(false);
  const abort = useRef<AbortController | null>(null);
  const st = llmStatus.value;

  useEffect(() => {
    void pollLlmStatus();
    return () => abort.current?.abort();
  }, []);

  const dirty = url.trim() !== s.ollamaUrl || model.trim() !== s.model;

  async function save(): Promise<boolean> {
    setBusy(true);
    setMsg(null);
    try {
      await saveSettings({ ollamaUrl: url.trim(), model: model.trim() });
      await pollLlmStatus();
      setMsg({ tone: "ok", text: "Saved." });
      return true;
    } catch (e) {
      setMsg({ tone: "err", text: errText(e) });
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function startPull() {
    if (dirty && !(await save())) return;
    const ac = new AbortController();
    abort.current = ac;
    setPulling(true);
    setMsg(null);
    setPull({ status: "starting" });
    try {
      for await (const ev of pullModel(model.trim(), ac.signal)) {
        if (ev.event === "progress") setPull({ status: ev.data.status, completed: ev.data.completed, total: ev.data.total });
        else if (ev.event === "error") {
          setMsg({ tone: "err", text: `Pull failed: ${ev.data.message}` });
          setPull(null);
        } else if (ev.event === "done") {
          setPull((p) => ({ status: "done", completed: p?.total, total: p?.total }));
          setMsg({ tone: "ok", text: `Pulled ${model.trim()}.` });
        }
      }
    } catch (e) {
      if ((e as Error)?.name !== "AbortError") setMsg({ tone: "err", text: errText(e) });
      else setMsg({ tone: "err", text: "Pull cancelled." });
    } finally {
      setPulling(false);
      abort.current = null;
      void pollLlmStatus();
    }
  }

  async function warmUp() {
    setWarming(true);
    setWarm(null);
    try {
      const r = await warmupLlm();
      setWarm(`Warm-up finished in ${r.ms} ms.`);
      void pollLlmStatus();
    } catch (e) {
      setWarm(`Warm-up failed: ${errText(e)}`);
    } finally {
      setWarming(false);
    }
  }

  const pct = pull?.total ? Math.min(100, Math.round(((pull.completed ?? 0) / pull.total) * 100)) : pull?.status === "done" ? 100 : null;

  return (
    <Card title="Model" class="st-card" aria-label="Model settings">
      <div class="st-field">
        <label class="label" for="st-url">Ollama URL</label>
        <input id="st-url" class="field" type="text" value={url} autoComplete="off" onInput={(e) => setUrl((e.target as HTMLInputElement).value)} />
      </div>
      <div class="st-field">
        <label class="label" for="st-model">Model name</label>
        <input id="st-model" class="field" type="text" list="st-models" value={model} autoComplete="off" onInput={(e) => setModel((e.target as HTMLInputElement).value)} />
        <datalist id="st-models">
          {SUGGESTED.map((m) => (
            <option key={m} value={m} />
          ))}
        </datalist>
      </div>
      <div class="st-actions">
        <Button variant="primary" disabled={!dirty || busy} onClick={() => void save()}>
          {busy ? "Saving..." : "Save model settings"}
        </Button>
        <Button disabled={pulling || !model.trim()} onClick={() => void startPull()} data-testid="pull-model">
          Pull model
        </Button>
        {pulling && <Button variant="ghost" onClick={() => abort.current?.abort()}>Cancel pull</Button>}
        <Button disabled={warming || pulling} onClick={() => void warmUp()}>
          {warming ? "Warming up..." : "Warm up"}
        </Button>
      </div>
      {msg && (
        <p class={msg.tone === "ok" ? "st-saved" : "st-err"} role={msg.tone === "err" ? "alert" : "status"}>
          {msg.text}
        </p>
      )}
      {warm && <p class="muted small">{warm}</p>}
      {pull && (
        <div data-testid="pull-progress">
          <div class="st-progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct ?? undefined} aria-label="Model download progress">
            <i style={`width:${pct ?? 5}%`} />
          </div>
          <div class="muted small" style="margin-top:6px">
            {pull.status}
            {pull.total ? `: ${gb(pull.completed ?? 0)} of ${gb(pull.total)} (${pct}%)` : ""}
          </div>
        </div>
      )}
      <p class="muted small">The pull runs through Ollama and needs the internet once. Apple Silicon: the larger E4B build; the friend's Intel laptop: the smaller E2B build (his speed is not measured yet).</p>

      <div class="stack" style="gap:8px" aria-live="polite" data-testid="llm-status">
        {!st ? (
          <StatusRow tone="idle">Status unknown: the pit server did not answer.</StatusRow>
        ) : (
          <>
            <StatusRow tone={st.reachable ? "ok" : "danger"}>{st.reachable ? `Ollama reachable at ${st.url}` : `Ollama not reachable at ${st.url}`}</StatusRow>
            <StatusRow tone={st.present ? "ok" : st.reachable ? "warn" : "idle"}>{st.present ? `${st.model} is pulled` : `${st.model} is not pulled yet`}</StatusRow>
            <StatusRow tone={st.loaded ? "ok" : "idle"}>{st.loaded ? "Loaded in memory" : "Not loaded in memory (the first answer after a start is slower)"}</StatusRow>
            <StatusRow tone="idle">{typeof st.lastLatencyMs === "number" ? `Last model call: ${st.lastLatencyMs} ms` : "No model call timed yet"}</StatusRow>
          </>
        )}
      </div>

      <Toggle
        label="Coach phrasing (LLM explanations)"
        hint="Off: the coach shows the plain template text instead of a model-written explanation. Symptom matching and lever choice are unchanged."
        checked={s.llmPhrasing}
        testId="toggle-llmPhrasing"
        onChange={(v) => void saveSettings({ llmPhrasing: v }).catch((e) => setMsg({ tone: "err", text: errText(e) }))}
      />

      <details class="st-details">
        <summary>Advanced</summary>
        <div class="st-field">
          <span class="label">Context size (num_ctx)</span>
          <input class="field" type="text" readOnly value={String(s.numCtx)} aria-label="num_ctx (read only)" />
          <span class="muted small">Fixed at {s.numCtx} to keep answers fast on a CPU-only laptop.</span>
        </div>
      </details>
    </Card>
  );
}
