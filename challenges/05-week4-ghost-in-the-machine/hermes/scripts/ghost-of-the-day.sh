#!/usr/bin/env bash
# Cron wrapper: a cron job runs a script file with no arguments, so the arguments live here.
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/haunt.sh" --source archive --seed daily --deploy "$@"
