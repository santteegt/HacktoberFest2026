#!/bin/bash
# Run a command inside the leash-hermes VM through a login shell (so ~/.local/bin is on PATH).
#   scripts/vm/run.sh 'hermes doctor'
# The command is sent on stdin, so quoting is the same as in a local shell.
printf '%s\n' "$*" | ssh -o BatchMode=yes leash-hermes 'zsh -l -s'
