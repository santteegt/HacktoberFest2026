// In-process registry of coach turns whose first segment (classify -> explain -> suspend) is still running (T7).
// The runId reaches the UI with `classified`/`suggestion`, so Apply can be tapped before the turn has suspended;
// decide/outcome call waitForStart(runId) first so they never resume a run that is not suspended yet.
const pending = new Map<string, Promise<void>>();

/** Marks a turn as starting; call the returned function when its first segment ends (success or failure). */
export function trackStart(runId: string): () => void {
  let done!: () => void;
  pending.set(
    runId,
    new Promise<void>((res) => {
      done = res;
    }),
  );
  return () => {
    pending.delete(runId);
    done();
  };
}

/** Resolves once the turn's first segment has finished (immediately when it is not running in this process). */
export async function waitForStart(runId: string): Promise<void> {
  await pending.get(runId);
}
