// Vault repository (T1). T0 stub with the function names from the T1 card; T3's `apply` step calls
// applySetupChanges and its `logOutcome` step calls setChangeOutcome. Functions use getDb() from server/db.ts.
import type {
  AddRunBody,
  ApplySetupResponse,
  CreateSessionBody,
  ImportResponse,
  PatchSessionBody,
  SaveSetupBody,
  SessionBundle,
} from "../../src/shared/api";
import type {
  Change,
  ChangeSource,
  ExportDump,
  Outcome,
  ParamValue,
  Run,
  SavedSetup,
  Session,
  Settings,
  SettingsPatch,
} from "../../src/shared/types";

const ni = (): never => {
  throw new Error("not implemented");
};

export async function createSession(_body: CreateSessionBody): Promise<Session> { return ni(); }
export async function listSessions(): Promise<Session[]> { return ni(); }
export async function getSessionBundle(_sessionId: string): Promise<SessionBundle> { return ni(); }
export async function patchSession(_sessionId: string, _body: PatchSessionBody): Promise<Session> { return ni(); }

/** Copy-on-write: one new setup row, one Change per changed param. */
export async function applySetupChanges(
  _sessionId: string,
  _values: Record<string, ParamValue>,
  _meta: { source: ChangeSource; leverId?: string; symptomId?: string; coachRunId?: string },
): Promise<ApplySetupResponse> { return ni(); }

export async function addRun(_sessionId: string, _body: AddRunBody): Promise<Run> { return ni(); }
export async function setChangeOutcome(_changeId: string, _outcome: Outcome, _outcomeRunId?: string): Promise<Change> { return ni(); }
export async function listSaved(): Promise<SavedSetup[]> { return ni(); }
export async function saveSetup(_body: SaveSetupBody): Promise<SavedSetup> { return ni(); }
export async function deleteSaved(_id: string): Promise<void> { return ni(); }
export async function exportAll(): Promise<ExportDump> { return ni(); }
/** Writes var/backups/<ts>.json before importing. */
export async function importAll(_dump: ExportDump): Promise<ImportResponse> { return ni(); }
export async function resetAll(): Promise<void> { return ni(); }
export async function getSettings(): Promise<Settings> { return ni(); }
export async function putSettings(_patch: SettingsPatch): Promise<Settings> { return ni(); }
