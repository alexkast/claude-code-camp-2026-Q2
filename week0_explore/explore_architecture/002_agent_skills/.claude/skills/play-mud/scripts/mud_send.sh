#!/bin/bash
# Sends one command to a running MUD session and prints the new server
# output, with ANSI color codes and carriage returns stripped so it's
# readable as plain text.
#
# Usage: mud_send.sh <session-dir> "<command>"
#
# Example: mud_send.sh .mud-session "look"
#          mud_send.sh .mud-session "n"
#          mud_send.sh .mud-session "list"
set -euo pipefail

SESSION_DIR="${1:?usage: mud_send.sh <session-dir> \"<command>\"}"
CMD="${2:?usage: mud_send.sh <session-dir> \"<command>\"}"
FIFO="$SESSION_DIR/cmd.fifo"
LOG="$SESSION_DIR/session.log"

before=$(wc -c < "$LOG")
echo "$CMD" > "$FIFO"

# Poll until new output stops growing. The game can take a moment to
# respond, especially right after a room change, a shop transaction, or
# when combat/other-player messages are also arriving, so this waits for
# quiet rather than assuming a fixed reply size.
prev_size=-1
for _ in $(seq 1 20); do
    sleep 0.25
    cur_size=$(wc -c < "$LOG")
    if [ "$cur_size" = "$prev_size" ] && [ "$cur_size" -gt "$before" ]; then
        break
    fi
    prev_size=$cur_size
done

LC_ALL=C tail -c +"$((before + 1))" "$LOG" | LC_ALL=C perl -pe 's/\x1b\[[0-9;]*[a-zA-Z]//g; s/\r//g'
