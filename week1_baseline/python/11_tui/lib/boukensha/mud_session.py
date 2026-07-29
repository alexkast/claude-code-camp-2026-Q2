from __future__ import annotations

import socket
import threading
import time
from typing import Any


class MudSessionError(Exception):
    pass


class MudConnectionError(MudSessionError):
    pass


class MudLoginError(MudSessionError):
    pass


class MudTimeoutError(MudSessionError):
    pass


# Telnet protocol bytes we recognise. We don't negotiate -- we just consume
# and discard IAC sequences so they don't pollute the buffer.
_IAC = 0xFF
_DONT = 0xFE
_DO = 0xFD
_WONT = 0xFC
_WILL = 0xFB
_SB = 0xFA
_SE = 0xF0

_NEGOTIATION_BYTES = {_WILL, _WONT, _DO, _DONT}


class MudSession:
    """Long-lived telnet connection to a CircleMUD server.

    A background thread continuously drains the socket into an internal
    buffer, stripping telnet IAC negotiation bytes. The agent loop sends a
    command and then calls `read_until_quiet` (or `read_until` for a known
    prompt) to collect both the command's response and any async chatter
    that arrived in the meantime.

    This is an original Python reimplementation of the Ruby `mud_manager`
    gem's `MudManager::Session` class (vendored at
    week0_explore/mud_manager/lib/mud_manager/session.rb), not a wrapper
    around any published package.
    """

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 4000
    DEFAULT_TIMEOUT = 10.0
    PROMPT_SENTINEL = "> "

    def __init__(
        self,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.host = host
        self.port = port
        self._timeout = timeout
        self._socket: socket.socket | None = None
        self._reader: threading.Thread | None = None
        self._buffer = ""
        self._cond = threading.Condition()
        self._closed = False
        self._last_recv_at: float | None = None

    def open(self) -> "MudSession":
        if self._socket is not None:
            raise MudSessionError("already open")
        try:
            self._socket = socket.create_connection((self.host, self.port))
        except OSError as e:
            raise MudConnectionError(f"connect {self.host}:{self.port} failed: {e}") from e
        self._closed = False
        self._start_reader()
        return self

    def is_open(self) -> bool:
        return self._socket is not None and not self._closed

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
        if self._reader is not None:
            self._reader.join(1)
        self._socket = None
        self._reader = None

    # Send a command. Accepts a string, `None` (Ruby's :return/:enter
    # sentinel -> blank line), or anything with a `.raw` attribute (e.g. a
    # mud_primitives.Command). A trailing newline is appended.
    def send_command(self, command: Any) -> str:
        if not self.is_open():
            raise MudSessionError("session not open")
        if command is None:
            line = ""
        elif hasattr(command, "raw"):
            line = command.raw
        else:
            line = str(command)
        assert self._socket is not None
        self._socket.sendall((line + "\r\n").encode("utf-8"))
        return line

    # Drain whatever is currently buffered and return it. Non-blocking.
    def drain(self) -> str:
        with self._cond:
            out, self._buffer = self._buffer, ""
            return out

    # Block until `quiet_seconds` have elapsed with no new bytes arriving,
    # or `timeout` total seconds pass. Returns whatever accumulated.
    def read_until_quiet(self, quiet_seconds: float = 1.0, *, timeout: float | None = None) -> str:
        if not self.is_open():
            raise MudSessionError("session not open")
        deadline = time.monotonic() + (timeout or self._timeout)
        with self._cond:
            while True:
                remaining_total = deadline - time.monotonic()
                if remaining_total <= 0:
                    break

                if (
                    self._last_recv_at is not None
                    and (time.monotonic() - self._last_recv_at) >= quiet_seconds
                    and self._buffer
                ):
                    break

                if self._last_recv_at is not None and self._buffer:
                    wait_for = quiet_seconds - (time.monotonic() - self._last_recv_at)
                else:
                    wait_for = remaining_total
                wait_for = min(wait_for, remaining_total)
                if wait_for <= 0:
                    break
                self._cond.wait(wait_for)

            out, self._buffer = self._buffer, ""
            return out

    # Block until the buffer contains the given pattern (str or compiled
    # regex), then return everything up to and including the match. Raises
    # MudTimeoutError if `timeout` seconds pass without a match.
    def read_until(self, pattern: Any, *, timeout: float | None = None) -> str:
        import re

        if not self.is_open():
            raise MudSessionError("session not open")
        regexp = pattern if hasattr(pattern, "search") else re.compile(re.escape(pattern))
        deadline = time.monotonic() + (timeout or self._timeout)
        with self._cond:
            while True:
                m = regexp.search(self._buffer)
                if m:
                    cut = m.end()
                    out = self._buffer[:cut]
                    self._buffer = self._buffer[cut:]
                    return out
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise MudTimeoutError(f"read_until {pattern!r} after {timeout}s")
                if self._closed:
                    raise MudConnectionError("socket closed while waiting")
                self._cond.wait(remaining)

    # CircleMUD terminates every command response with a prompt that ends in
    # "> " (greater-than space). Waiting for that sentinel is faster and more
    # deterministic than relying on a silence window -- it returns as soon as
    # the server signals it has finished processing the command.
    #
    # Falls back to draining the buffer if the prompt is never seen within
    # the timeout (e.g. during combat when extra async lines may slip in).
    def read_until_prompt(self, *, timeout: float | None = None) -> str:
        try:
            return self.read_until(self.PROMPT_SENTINEL, timeout=timeout)
        except MudTimeoutError:
            return self.drain()

    # Walk the CircleMUD login dance.
    def login(self, username: str, password: str) -> str:
        import re

        self.read_until(re.compile(r"By what name do you wish to be known.*\?", re.IGNORECASE))

        self.send_command(username)

        self.read_until(re.compile(r"Password", re.IGNORECASE))

        self.send_command(password)

        output = self.read_until(re.compile(r"Welcome|Reconnecting|Wrong password", re.IGNORECASE))
        if re.search(r"Reconnecting", output, re.IGNORECASE):
            pass  # already in-world, skip menu
        elif re.search(r"Welcome", output, re.IGNORECASE):
            self.send_command(None)  # enter for main menu
            self.send_command("1")  # enter the game
            self.read_until_quiet()
        elif re.search(r"Wrong password", output, re.IGNORECASE):
            raise MudLoginError("wrong password")
        return output

    # ----- internals -----

    def _start_reader(self) -> None:
        def _reader_loop() -> None:
            try:
                while True:
                    assert self._socket is not None
                    chunk = self._socket.recv(4096)
                    if not chunk:
                        break
                    text = self._strip_iac(chunk)
                    if text:
                        with self._cond:
                            self._buffer += text
                            self._last_recv_at = time.monotonic()
                            self._cond.notify_all()
            except OSError:
                pass  # remote closed -- fall through
            finally:
                with self._cond:
                    self._closed = True
                    self._cond.notify_all()

        self._reader = threading.Thread(target=_reader_loop, daemon=True)
        self._reader.start()

    # Telnet protocol IAC stripper. The MUD may interleave:
    #   IAC (WILL|WONT|DO|DONT) <option>            -- 3 bytes
    #   IAC SB <option> ... IAC SE                  -- variable
    #   IAC IAC                                     -- literal 0xFF byte
    # We discard all of them. CircleMUD's negotiation is mostly echo
    # toggling around the password prompt, which we don't honor.
    def _strip_iac(self, data: bytes) -> str:
        out = bytearray()
        i = 0
        n = len(data)
        while i < n:
            b = data[i]
            if b == _IAC:
                nxt = data[i + 1] if i + 1 < n else None
                if nxt is None:
                    break
                elif nxt == _IAC:
                    out.append(0xFF)
                    i += 2
                elif nxt in _NEGOTIATION_BYTES:
                    i += 3
                elif nxt == _SB:
                    j = i + 2
                    while j < n and not (data[j] == _IAC and j + 1 < n and data[j + 1] == _SE):
                        j += 1
                    i = j + 2
                else:
                    i += 2
            else:
                out.append(b)
                i += 1
        return out.decode("utf-8", errors="replace")
