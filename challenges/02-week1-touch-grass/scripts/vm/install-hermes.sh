#!/bin/bash
# Run INSIDE the macOS VM (after install-clt.sh). Installs Hermes Agent with the official installer.
set -euo pipefail
git --version >/dev/null 2>&1 || { echo "git is not usable yet: run install-clt.sh first"; exit 1; }
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --non-interactive
echo
echo "Open a new shell (or: source ~/.zshrc), then run: hermes doctor"
