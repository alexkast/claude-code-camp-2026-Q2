#!/usr/bin/env python3
"""
Persistent tbaMUD session driver.

Holds one TCP connection to the MUD open for the life of this process. Reads
commands from a FIFO (one per line) and forwards each to the server; appends
everything the server sends back to a log file.

Why a long-lived driver instead of a "connect, run a few commands, quit"
script: the MUD's login is an interactive, prompt-driven sequence (not one
command with flags), and the game itself is a long-lived async session --
combat rounds and other players' actions can arrive without you sending
anything. A short one-shot script cannot reliably ride out that back-and-forth
because the exact number and timing of prompts varies. One process, fed one
command at a time and reading until the server goes quiet, matches how the
game actually behaves.

Usage:
    MUD_USER=dummy MUD_PASS=helloworld python3 mud_driver.py <fifo> <logfile> [host] [port]

Normally you won't call this directly -- use mud_start.sh, which creates the
FIFO/log and waits for the ===READY=== marker for you.
"""
import os
import select
import socket
import sys
import time


def drain(sock: socket.socket, log, quiet_seconds: float = 1.5, hard_timeout: float = 8.0) -> str:
    """Read everything the server sends until it goes quiet for
    `quiet_seconds`, or `hard_timeout` total elapses. The hard timeout is a
    safety net for situations that stream continuously (e.g. a room full of
    fighting mobs) so a single drain() call can never hang forever."""
    start = time.time()
    quiet_until = time.time() + quiet_seconds
    got = b""
    while time.time() < quiet_until and time.time() - start < hard_timeout:
        ready, _, _ = select.select([sock], [], [], 0.3)
        if ready:
            chunk = sock.recv(8192)
            if not chunk:
                break
            got += chunk
            log.write(chunk)
            log.flush()
            quiet_until = time.time() + quiet_seconds
    return got.decode("utf-8", errors="ignore")


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: mud_driver.py <fifo> <logfile> [host] [port]", file=sys.stderr)
        sys.exit(1)

    fifo_path = sys.argv[1]
    log_path = sys.argv[2]
    host = sys.argv[3] if len(sys.argv) > 3 else "localhost"
    port = int(sys.argv[4]) if len(sys.argv) > 4 else 4000

    user = os.environ.get("MUD_USER")
    password = os.environ.get("MUD_PASS")
    if not user or not password:
        print("MUD_USER and MUD_PASS must be set in the environment", file=sys.stderr)
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    log = open(log_path, "ab")

    # --- Login ---
    # This automated flow covers logging into an EXISTING character, which is
    # the common case (a fixed test account like dummy/helloworld). See
    # references/protocol.md for the NEW-character flow, which asks several
    # more questions (confirm name, retype password, sex, class) and is not
    # automated here -- drive it by hand with mud_send.sh if you ever need it.
    drain(sock, log, 1.5)                       # banner, "By what name..."
    sock.sendall((user + "\r\n").encode())
    after_name = drain(sock, log, 1.5)           # "Password:" for an existing char,
                                                  # or "...(Y/N)?" for a new one

    if "Password" in after_name:
        sock.sendall((password + "\r\n").encode())
        drain(sock, log, 1.5)                    # welcome banner + "PRESS RETURN:"
        sock.sendall(b"\r\n")
        drain(sock, log, 1.5)                    # main menu (0-5 choices)
        sock.sendall(b"1\r\n")                   # 1) Enter the game
        drain(sock, log, 2.0)                    # starting room description
        log.write(b"\n===READY===\n")
    else:
        log.write(
            b"\n===LOGIN-NEEDS-ATTENTION===\n"
            b"Did not see a 'Password:' prompt after sending the username -- "
            b"this looks like a NEW-character creation flow instead of a login "
            b"to an existing character. See references/protocol.md for the "
            b"prompts to expect, and drive the rest by hand with mud_send.sh.\n"
        )
    log.flush()

    # --- Serve commands from the FIFO, one per line, until told to stop ---
    while True:
        with open(fifo_path, "r") as fifo:
            line = fifo.readline()
        if not line:
            continue
        cmd = line.rstrip("\n")
        if cmd == "__QUIT__":
            break
        log.write(("\n>>> " + cmd + "\n").encode())
        log.flush()
        sock.sendall((cmd + "\r\n").encode())
        drain(sock, log, 1.8)

    sock.close()
    log.close()


if __name__ == "__main__":
    main()
