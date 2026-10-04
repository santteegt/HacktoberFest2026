// Error type thrown by vault functions; server/vault/app.ts maps it to the contract `{ error, stage }` response.
import type { ContentfulStatusCode } from "hono/utils/http-status";

export class VaultError extends Error {
  constructor(
    public status: ContentfulStatusCode,
    message: string,
    public stage = "vault",
  ) {
    super(message);
    this.name = "VaultError";
  }
}
