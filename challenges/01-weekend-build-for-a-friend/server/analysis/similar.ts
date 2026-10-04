// Race-day finder: similar conditions (T8; plan 4.6). T0 stub.
import type { SavedSetup, Setup, SetupValues, SimilarHit, TrackConditions } from "../../src/shared/types";

export function similarSetups(
  _today: TrackConditions,
  _saved: SavedSetup[],
  _current: SetupValues,
  _setups: Map<string, Setup>,
): SimilarHit[] {
  throw new Error("not implemented");
}
