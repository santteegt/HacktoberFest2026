#!/usr/bin/env bash
# Run a command inside the VM through a login shell, so ~/.local/bin (hermes, leashctl) is on PATH.
#   ops/vm-run.sh 'hermes gateway status'
printf '%s\n' "$*" | ssh -o BatchMode=yes "${LEASH_VM_SSH:-leash-hermes}" 'zsh -l -s'
