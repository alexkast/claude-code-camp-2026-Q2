#!/bin/bash
# Starts a MUD session: creates a control FIFO and log file, launches
# mud_driver.py in the background, and waits until login finishes.
#
# Usage: MUD_USER=dummy MUD_PASS=helloworld mud_start.sh <session-dir> [host] [port]
#
#   session-dir  A directory to hold cmd.fifo, session.log, driver.pid.
#                Created if it doesn't exist. Use a fresh directory per
#                play session (e.g. under your scratchpad), not one shared
#                across unrelated sessions.
#
# On success, prints "Session ready." and the driver's PID.
# On failure (login didn't finish in time), prints the tail of session.log
# and exits non-zero -- read the full log to see what the server said.
set -euo pipefail

SESSION_DIR="${1:?usage: mud_start.sh <session-dir> [host] [port]}"
HOST="${2:-localhost}"
PORT="${3:-4000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${MUD_USER:-}" ] || [ -z "${MUD_PASS:-}" ]; then
    echo "MUD_USER and MUD_PASS must be set in the environment" >&2
    exit 1
fi

mkdir -p "$SESSION_DIR"
FIFO="$SESSION_DIR/cmd.fifo"
LOG="$SESSION_DIR/session.log"

rm -f "$FIFO"
mkfifo "$FIFO"
: > "$LOG"

nohup python3 "$SCRIPT_DIR/mud_driver.py" "$FIFO" "$LOG" "$HOST" "$PORT" \
    > "$SESSION_DIR/driver.out" 2>&1 &
echo $! > "$SESSION_DIR/driver.pid"

# Wait for the ===READY=== marker (or a login-needs-attention marker).
for _ in $(seq 1 50); do
    if grep -q "===READY===" "$LOG" 2>/dev/null; then
        echo "Session ready. PID $(cat "$SESSION_DIR/driver.pid")"
        exit 0
    fi
    if grep -q "===LOGIN-NEEDS-ATTENTION===" "$LOG" 2>/dev/null; then
        echo "Login needs manual attention -- see $LOG" >&2
        tail -n 20 "$LOG" >&2
        exit 1
    fi
    sleep 0.3
done

echo "Login did not complete within 15s -- check $LOG" >&2
tail -n 20 "$LOG" >&2
exit 1
