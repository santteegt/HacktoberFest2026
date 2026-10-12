#!/usr/bin/env bash
# Reverse SSH tunnel from the Mac into the VM:
#   VM 127.0.0.1:11434 -> Mac Ollama      VM 127.0.0.1:8787 -> Mac Leash tool server
# Both ports are loopback-only on each side. Run by the com.leash.tunnel LaunchAgent, which restarts it.
set -u
ALIAS="${LEASH_VM_SSH:-leash-hermes}"
OPTS=(-o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=20 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes)

# Wait for the VM's SSH to answer (it may be starting, or the Mac may have just woken).
until ssh "${OPTS[@]}" "$ALIAS" true 2>/dev/null; do
  echo "$(date '+%F %T') waiting for ssh to $ALIAS"; sleep 10
done

# After a sleep/wake the VM's sshd can keep an old, dead forward bound to these ports, which would make
# the new one fail. Free them first (only sshd processes owned by the VM user are touched).
ssh "${OPTS[@]}" "$ALIAS" 'for p in 11434 8787; do for pid in $(lsof -nP -iTCP:$p -sTCP:LISTEN -t 2>/dev/null); do
  ps -o comm= -p "$pid" | grep -q ssh && kill "$pid"; done; done' 2>/dev/null || true
sleep 1

echo "$(date '+%F %T') opening tunnel"
exec ssh -N "${OPTS[@]}" \
  -R 127.0.0.1:11434:127.0.0.1:11434 \
  -R 127.0.0.1:8787:127.0.0.1:8787 \
  "$ALIAS"
