from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ._state import config, is_debug


class Logger:
    DEFAULT_SESSION_DIR = "sessions"

    def __init__(
        self,
        *,
        session_id: str | None = None,
        dir: str | None = None,
        log: str | None = None,
        snapshot: dict[str, Any] | None = None,
    ) -> None:
        self.session_id = session_id or self._generate_session_id()
        self.path = log or str(Path(dir or self._default_dir()) / f"{self.session_id}.jsonl")

        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._log_io = open(self.path, "a")
        self._subscribers: list[Callable[[dict[str, Any]], None]] = []
        self._write_log({"phase": "session_start", **(snapshot or {})})

    def turn(self, *, n: int) -> None:
        self._write_log({"phase": "turn", "n": n})

    def iteration(self, *, n: int, max: int) -> None:
        self._write_log({"phase": "iteration", "n": n, "max": max})

    def limit_reached(self, *, kind: str, n: int, max: int) -> None:
        self._write_log({"phase": "limit_reached", "kind": kind, "n": n, "max": max})

    def turn_end(self, *, reason: str, iterations: int, tokens: Any = None) -> None:
        self._write_log(
            {"phase": "turn_end", "reason": reason, "iterations": iterations, "tokens": tokens}
        )

    def prompt(self, *, messages: list[Any], tools: dict[str, Any], context_window: int) -> None:
        self._write_log(
            {
                "phase": "prompt",
                "message_count": len(messages),
                "messages": [self._serialize_message(m) for m in messages],
                "tool_count": len(tools),
                "tools": list(tools.keys()),
                "context_window": context_window,
            }
        )

    def compaction(self, *, before: int, dropped: int, context_window: int) -> None:
        self._write_log(
            {"phase": "compaction", "before": before, "dropped": dropped, "context_window": context_window}
        )

    def tool_call(self, *, name: str, args: dict[str, Any]) -> None:
        self._write_log({"phase": "tool_call", "name": name, "args": args})

    def tool_result(
        self, *, name: str, result: Any, ok: bool = True, error: str | None = None
    ) -> None:
        self._write_log(
            {"phase": "tool_result", "name": name, "result": str(result), "ok": ok, "error": error}
        )

    def response(self, *, text: str, usage: dict[str, Any] | None = None, stop_reason: str | None = None) -> None:
        self._write_log(
            {
                "phase": "response",
                "text": str(text).strip(),
                "usage": usage,
                "stop_reason": stop_reason,
            }
        )

    def reasoning(self, *, text: str, redacted: bool = False) -> None:
        self._write_log({"phase": "reasoning", "text": str(text), "redacted": redacted})

    def plan(self, *, text: str) -> None:
        self._write_log({"phase": "plan", "text": str(text).strip()})

    def raw(self, *, data: Any) -> None:
        if not is_debug():
            return

        self._write_log({"phase": "raw", "data": data})

    def subscribe(self, callback: Callable[[dict[str, Any]], None]) -> None:
        self._subscribers.append(callback)

    def close(self) -> None:
        if self._log_io is not None:
            self._log_io.close()

    def _default_dir(self) -> str:
        return str(Path(config().dir) / self.DEFAULT_SESSION_DIR)

    def _write_log(self, event: dict[str, Any]) -> None:
        self._log_io.write(
            json.dumps({**event, "session_id": self.session_id, "at": self._now_iso()}) + "\n"
        )
        self._log_io.flush()
        for subscriber in self._subscribers:
            subscriber(event)

    def _now_iso(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _generate_session_id(self) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-{secrets.token_hex(4)}"

    def _serialize_message(self, msg: Any) -> dict[str, Any]:
        return {"role": msg.role, "content": msg.content}
