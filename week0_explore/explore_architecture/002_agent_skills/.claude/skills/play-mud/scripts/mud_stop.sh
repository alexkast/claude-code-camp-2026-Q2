#!/bin/bash
# Cleanly ends a MUD session started with mud_start.sh: tells the driver to
# quit, then kills the process if it's still around.
#
# Usage: mud_stop.sh <session-dir>
set -euo pipefail

SESSION_DIR="${1:?usage: mud_stop.sh <session-dir>}"
FIFO="$SESSION_DIR/cmd.fifo"

if [ -p "$FIFO" ]; then
    echo "__QUIT__" > "$FIFO" || true
fi
sleep 0.5

if [ -f "$SESSION_DIR/driver.pid" ]; then
    kill "$(cat "$SESSION_DIR/driver.pid")" 2>/dev/null || true
fi

echo "Session stopped."
