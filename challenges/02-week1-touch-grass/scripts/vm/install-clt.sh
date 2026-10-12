#!/bin/bash
# Run INSIDE the macOS VM. Installs Apple's Command Line Tools without the GUI dialog,
# because git on a fresh macOS is only a stub until they exist. Needs sudo (asks for the VM user's password).
set -euo pipefail
if xcode-select -p >/dev/null 2>&1 && git --version >/dev/null 2>&1; then
  echo "Command Line Tools already installed: $(git --version)"; exit 0
fi
MARK=/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
touch "$MARK"; trap 'rm -f "$MARK"' EXIT
echo "Looking for the Command Line Tools package..."
LABEL="$(softwareupdate -l 2>&1 | grep -E 'Label: Command Line Tools' | sed -E 's/^[* ]*Label: //' | sort -V | tail -1)"
[ -n "$LABEL" ] || { echo "No Command Line Tools package offered by softwareupdate. Output was:"; softwareupdate -l 2>&1 | tail -15; exit 1; }
echo "Installing: $LABEL (this downloads about 1 GB)"
sudo softwareupdate -i "$LABEL" --verbose
echo "Done: $(git --version)"
