#!/usr/bin/env bash
# Cron wrapper: one incident ghost a week; the seed is the ISO week so a retry picks the same one.
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/haunt.sh" --source incident --seed "week-$(date -u +%G-%V)" --deploy "$@"
