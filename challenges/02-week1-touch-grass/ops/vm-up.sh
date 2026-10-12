#!/usr/bin/env bash
# Make sure the Lume VM is running. Safe to run any time; does nothing when it is already up.
# Run by the com.leash.vm LaunchAgent at load and every 2 minutes.
#
# "Running" means the VM answers on SSH. `lume ls` is not trusted on its own: it reported "stopped" for a
# VM that was running (started by an earlier foreground `lume run`), and starting a second copy is wrong.
set -u
VM="${LEASH_VM:-leash-hermes}"
ALIAS="${LEASH_VM_SSH:-leash-hermes}"
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin"
if ssh -o BatchMode=yes -o ConnectTimeout=5 "$ALIAS" true 2>/dev/null; then exit 0; fi
LUME="$(command -v lume || echo "$HOME/.local/bin/lume")"
state="$("$LUME" ls 2>/dev/null | awk -v n="$VM" '$1==n {print $0}')"
if printf '%s' "$state" | grep -q "running"; then
  echo "$(date '+%F %T') VM $VM is running but SSH does not answer yet; waiting"; exit 0
fi
echo "$(date '+%F %T') VM $VM not running and SSH does not answer, starting it"
exec "$LUME" run "$VM" --display none --detach
