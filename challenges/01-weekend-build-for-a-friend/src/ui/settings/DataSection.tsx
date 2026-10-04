// Settings > Data (T4c): export JSON (download), import JSON (counts first, then apply), reset (type RESET).
import { useRef, useState } from "preact/hooks";
import { exportAll, importAll, resetAll } from "../../api/client";
import { ExportDump } from "../../shared/schemas";
import type { ExportDump as ExportDumpT } from "../../shared/types";
import { Button, Card } from "../app/components";
import { bootstrap } from "../app/bootstrap";
import { bindStagedToSession } from "../setup/staged";
import { currentSetup, session } from "../store";
import { errText } from "./state";

type Counts = Record<string, number>;

const COUNT_LABELS: [string, string][] = [
  ["sessions", "sessions"],
  ["runs", "runs"],
  ["changes", "setup changes"],
  ["setups", "setup rows"],
  ["savedSetups", "saved setups"],
  ["settings", "settings"],
];

function countsOf(d: ExportDumpT): Counts {
  const t = d.tables;
  return { sessions: t.sessions.length, runs: t.runs.length, changes: t.changes.length, setups: t.setups.length, savedSetups: t.savedSetups.length, settings: t.settings.length };
}

function CountGrid({ counts }: { counts: Counts }) {
  return (
    <div class="st-counts">
      {COUNT_LABELS.map(([k, label]) => (
        <div class="st-count" key={k} data-testid={`count-${k}`}>
          <b>{counts[k] ?? 0}</b>
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

/** After the vault changed under the app: drop staged edits and the open session, then reload everything. */
async function reloadAll(): Promise<void> {
  bindStagedToSession(null);
  session.value = null;
  currentSetup.value = null;
  await bootstrap();
}

export function DataSection() {
  const [msg, setMsg] = useState<{ tone: "ok" | "err"; text: string } | null>(null);
  const [busy, setBusy] = useState<"export" | "import" | "reset" | null>(null);
  const [pending, setPending] = useState<{ name: string; dump: ExportDumpT } | null>(null);
  const [applied, setApplied] = useState<Counts | null>(null);
  const [word, setWord] = useState("");
  const file = useRef<HTMLInputElement>(null);

  async function doExport() {
    setBusy("export");
    setMsg(null);
    try {
      const dump = await exportAll();
      const blob = new Blob([JSON.stringify(dump, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const stamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, "");
      a.href = url;
      a.download = `rc-pit-export-${stamp}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      const c = countsOf(dump);
      setMsg({ tone: "ok", text: `Exported ${c.sessions} sessions, ${c.runs} runs, ${c.savedSetups} saved setups as ${a.download}.` });
    } catch (e) {
      setMsg({ tone: "err", text: errText(e) });
    } finally {
      setBusy(null);
    }
  }

  async function onFile(e: Event) {
    const input = e.target as HTMLInputElement;
    const f = input.files?.[0];
    input.value = "";
    if (!f) return;
    setMsg(null);
    setApplied(null);
    setPending(null);
    try {
      const json: unknown = JSON.parse(await f.text());
      const r = ExportDump.safeParse(json);
      if (!r.success) {
        const issue = r.error.issues[0];
        setMsg({ tone: "err", text: `${f.name} is not a pit export (${issue?.path.join(".") || "root"}: ${issue?.message ?? "invalid"}).` });
        return;
      }
      setPending({ name: f.name, dump: r.data as ExportDumpT });
    } catch (e2) {
      setMsg({ tone: "err", text: `Could not read ${f.name}: ${errText(e2)}` });
    }
  }

  async function applyImport() {
    if (!pending) return;
    setBusy("import");
    setMsg(null);
    try {
      const res = await importAll(pending.dump);
      setApplied(res.counts as Counts);
      setMsg({ tone: "ok", text: `Imported ${pending.name}. The vault now has what was in the file.` });
      setPending(null);
      await reloadAll();
    } catch (e) {
      setMsg({ tone: "err", text: errText(e) });
    } finally {
      setBusy(null);
    }
  }

  async function doReset() {
    setBusy("reset");
    setMsg(null);
    setApplied(null);
    try {
      await resetAll();
      setWord("");
      setMsg({ tone: "ok", text: "Reset done: sessions, runs, changes and saved setups are cleared. Settings were kept." });
      await reloadAll();
    } catch (e) {
      setMsg({ tone: "err", text: errText(e) });
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card title="Data" class="st-card st-wide" aria-label="Data">
      <p class="muted small">Everything lives in one local file on this computer. Export is a full copy you can keep or move to another laptop.</p>
      <div class="st-actions">
        <Button disabled={busy !== null} onClick={() => void doExport()} data-testid="export-json">
          {busy === "export" ? "Exporting..." : "Export JSON"}
        </Button>
        <Button disabled={busy !== null} onClick={() => file.current?.click()} data-testid="import-json">
          Import JSON
        </Button>
        <input ref={file} type="file" accept="application/json,.json" class="sr-only" tabIndex={-1} aria-label="Choose an export file" data-testid="import-file" onChange={(e) => void onFile(e)} />
      </div>

      {pending && (
        <div class="st-note" data-testid="import-preview">
          <p style="margin-bottom:8px">
            <b>{pending.name}</b> contains:
          </p>
          <CountGrid counts={countsOf(pending.dump)} />
          <p style="margin:8px 0">Importing replaces everything in the vault now with this file. The server writes a backup of the current vault first.</p>
          <div class="st-actions">
            <Button variant="warn" disabled={busy !== null} onClick={() => void applyImport()} data-testid="apply-import">
              {busy === "import" ? "Importing..." : "Apply import"}
            </Button>
            <Button variant="ghost" disabled={busy !== null} onClick={() => setPending(null)}>Cancel</Button>
          </div>
        </div>
      )}
      {applied && (
        <div data-testid="import-result">
          <p class="muted small" style="margin-bottom:6px">Rows now in the vault:</p>
          <CountGrid counts={applied} />
        </div>
      )}

      <div class="st-note" data-tone="warn">
        <p style="margin-bottom:8px">
          <b>Reset</b> clears sessions, runs, changes and saved setups. Settings are kept and a backup is written first. Type <code>RESET</code> to enable it.
        </p>
        <div class="st-actions">
          <input class="field" style="max-width:220px" type="text" value={word} placeholder="RESET" aria-label="Type RESET to confirm" autoComplete="off" data-testid="reset-word" onInput={(e) => setWord((e.target as HTMLInputElement).value)} />
          <Button variant="danger" disabled={word !== "RESET" || busy !== null} onClick={() => void doReset()} data-testid="reset-all">
            {busy === "reset" ? "Resetting..." : "Reset"}
          </Button>
        </div>
      </div>
      {msg && (
        <p class={msg.tone === "ok" ? "st-saved" : "st-err"} role={msg.tone === "err" ? "alert" : "status"} data-testid="data-msg">
          {msg.text}
        </p>
      )}
    </Card>
  );
}
