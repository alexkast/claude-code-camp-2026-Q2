from __future__ import annotations

import queue
import threading
import time
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Input, RichLog, Static

from .agent import Agent
from .errors import TurnCancelled

# TUI powered by Textual -- there is no Python equivalent of the Ruby version's
# charm (bubbletea + lipgloss + bubbles) stack, so this is a from-scratch
# reimplementation of the same four-zone layout and behavior, not a mechanical
# translation. See docs/plans/python_port/11_tui for the design discussion.

TICK_SECONDS = 0.06

SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

# Thresholds for context-usage colour coding.
CTX_WARN_PCT = 70
CTX_ALERT_PCT = 85

# Same hex values as Ruby's ANSI_COLORS (lipgloss). Textual's named colors
# (e.g. "bright_black") use different naming conventions than lipgloss's, so
# hex values keep the actual rendered colors identical to Ruby's.
CYAN = "#00ffff"
BRIGHT_BLACK = "#808080"
YELLOW = "#ffcc00"
RED = "#ff5555"


class BoukenshaApp(App[None]):
    """Wraps a Repl instance and replaces its raw print()/input() I/O with a
    structured four-zone display:

        ┌──────────────────────────────────────────────┐
        │  conversation viewport (scrollable)           │
        ├──────────────────────────────────────────────┤
        │  ⟳ live progress line (hidden when idle)     │
        ├──────────────────────────────────────────────┤
        │  boukensha> input box                         │
        ├──────────────────────────────────────────────┤
        │  status line (always-on)                      │
        └──────────────────────────────────────────────┘

    The Repl continues to own session logic (turn counting, /commands, Agent
    dispatch). BoukenshaApp registers output/event callbacks on the Repl and
    drives the live progress line off Logger.subscribe events.

    The agent runs on a Textual worker thread so the UI stays responsive
    during long turns; Esc requests cooperative cancellation via
    Repl.interrupt() (see agent.py's cancel_event / TurnCancelled).

    The idle progress line and status line read context-window usage
    (Context.current_tokens/context_window/usage_pct) directly rather than
    keeping a separate cumulative session counter -- so usage reflects what
    the *next* call will actually send, and drops correctly after /clear or
    /compact.
    """

    CSS = """
    RichLog {
        height: 1fr;
    }
    #progress {
        height: 1;
        color: cyan;
    }
    #status {
        height: 1;
        color: white;
        background: #808080;
    }
    Input {
        border: none;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+d", "quit", "Quit", show=False),
        Binding("escape", "interrupt_turn", "Interrupt", show=False),
        Binding("ctrl+l", "clear_conversation", "Clear", show=False),
        Binding("pageup", "scroll_up", "Scroll up", show=False),
        Binding("pagedown", "scroll_down", "Scroll down", show=False),
    ]

    def __init__(self, repl: Any) -> None:
        super().__init__()
        self.repl = repl
        self.context = repl.context
        self._events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._app_thread_id: int | None = None

        self._turn_count = 0

        self._live = self._fresh_live_state()

    def _fresh_live_state(self) -> dict[str, Any]:
        return {
            "active": False,
            "spinner_idx": 0,
            "start_time": None,
            "elapsed": 0.0,
            "current_action": "idle",
            "iteration": 0,
            "tool_call_count": 0,
            "turn_input_tokens": 0,
            "turn_output_tokens": 0,
        }

    # ── Textual app interface ───────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield RichLog(id="viewport", wrap=True, markup=False, auto_scroll=True)
        yield Static(id="progress", markup=False)
        yield Input(placeholder="Type a message…", id="input")
        yield Static(id="status", markup=False)

    def on_mount(self) -> None:
        self._app_thread_id = threading.get_ident()

        self.query_one("#viewport", RichLog).write(self.repl.banner())

        self.repl.on_output(self._on_repl_output)
        self.repl.logger.subscribe(self._on_log_event)

        self.query_one("#input", Input).focus()
        self.set_interval(TICK_SECONDS, self._tick)
        self._render_progress()
        self._render_status()

    # ── callbacks registered on the Repl/Logger ────────────────────────────
    # These fire on whichever thread is running the agent turn. Widget
    # mutation must happen on the app's own thread, so route through
    # call_from_thread unless we're already on it (calling call_from_thread
    # from the app's own thread would deadlock).

    def _on_repl_output(self, text: str) -> None:
        if threading.get_ident() == self._app_thread_id:
            self._append_conversation(text)
        else:
            self.call_from_thread(self._append_conversation, text)

    def _on_log_event(self, event: dict[str, Any]) -> None:
        # queue.Queue is thread-safe on its own; no marshaling needed here.
        self._events.put(event)

    def _append_conversation(self, text: str) -> None:
        self.query_one("#viewport", RichLog).write(text)

    # ── ticking (main thread only, via Textual's set_interval) ────────────

    def _tick(self) -> None:
        self._drain_events()
        if self._live["active"]:
            self._live["spinner_idx"] = (self._live["spinner_idx"] + 1) % len(SPINNER_FRAMES)
            if self._live["start_time"] is not None:
                self._live["elapsed"] = time.monotonic() - self._live["start_time"]
        self._render_progress()
        self._render_status()

    def _drain_events(self) -> None:
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            self._handle_event(event)

    def _handle_event(self, event: dict[str, Any]) -> None:
        phase = event.get("phase")

        if phase == "iteration":
            self._live["iteration"] = int(event.get("n") or 0)
            self._live["current_action"] = "Thinking…"

        elif phase == "tool_call":
            self._live["current_action"] = f"Calling tool: {event.get('name')}"
            self._live["tool_call_count"] += 1

        elif phase == "tool_result":
            self._live["current_action"] = "Awaiting result…"

        elif phase == "response":
            usage = event.get("usage")
            if usage:
                self._live["turn_input_tokens"] += int(usage.get("input_tokens") or 0)
                self._live["turn_output_tokens"] += int(usage.get("output_tokens") or 0)

        elif phase == "compaction":
            dropped = event.get("dropped")
            self._append_conversation(f"[context compacted — {dropped} messages dropped to free space]")

        elif phase == "turn_complete":
            self._live["active"] = False
            self._turn_count += 1

        elif phase == "turn_interrupted":
            self._append_conversation("[interrupted]")

        elif phase == "turn_error":
            self._live["active"] = False
            self._append_conversation(f"[error] {event.get('error')}")

    # ── rendering ───────────────────────────────────────────────────────────

    def _render_progress(self) -> None:
        progress = self.query_one("#progress", Static)
        if self._live["active"]:
            progress.styles.color = CYAN
            frame = SPINNER_FRAMES[self._live["spinner_idx"]]
            action = self._live["current_action"]
            iteration = self._live["iteration"]
            max_iter = Agent.MAX_ITERATIONS
            secs = int(self._live["elapsed"])
            itok = self._fmt_tokens(self._live["turn_input_tokens"])
            otok = self._fmt_tokens(self._live["turn_output_tokens"])
            calls = self._live["tool_call_count"]
            progress.update(
                f"{frame} {action}  (iter {iteration}/{max_iter} · {secs}s · "
                f"↑ {itok} · ↓ {otok} · {calls} calls)"
            )
        else:
            pct = self.context.usage_pct
            used = self._fmt_tokens(self.context.current_tokens)
            max_ = self._fmt_tokens(self.context.context_window)
            turns = self._turn_count
            progress.styles.color = self._ctx_color(pct)
            progress.update(f"  [ready]   ctx {used} / {max_} ({pct}%)   {turns} turns")

    def _render_status(self) -> None:
        status = self.query_one("#status", Static)
        ver = self.repl.version or "?.?.?"
        model = self.repl.model or "(model)"
        pct = self.context.usage_pct
        used = self._fmt_tokens(self.context.current_tokens)
        max_ = self._fmt_tokens(self.context.context_window)
        tools = self.context.tool_count
        clock = time.strftime("%H:%M:%S")

        ctx_indicator = " ⚠ " if pct >= CTX_ALERT_PCT else " "
        bar = f" boukensha v{ver} · {model}  ·  ctx {used}/{max_} ({pct}%){ctx_indicator}·  {tools} tools  ·  {clock} "
        status.update(bar)

    def _ctx_color(self, pct: int) -> str:
        if pct >= CTX_ALERT_PCT:
            return RED
        elif pct >= CTX_WARN_PCT:
            return YELLOW
        else:
            return BRIGHT_BLACK

    def _fmt_tokens(self, n: int) -> str:
        n = int(n)
        return f"{n / 1000.0:.1f}k" if n >= 1000 else str(n)

    # ── keyboard / input ─────────────────────────────────────────────────────

    def action_quit(self) -> None:
        self.exit()

    def action_interrupt_turn(self) -> None:
        self.repl.interrupt()

    def action_clear_conversation(self) -> None:
        self.repl.handle_command("/clear")
        self._turn_count = 0
        self.query_one("#viewport", RichLog).clear()

    def action_scroll_up(self) -> None:
        self.query_one("#viewport", RichLog).scroll_page_up()

    def action_scroll_down(self) -> None:
        self.query_one("#viewport", RichLog).scroll_page_down()

    def on_input_submitted(self, message: Input.Submitted) -> None:
        text = message.value.strip()
        message.input.value = ""
        if not text:
            return

        if text.startswith("/"):
            result = self.repl.handle_command(text)
            if result == "quit":
                self.exit()
                return
            if text == "/clear":
                self._turn_count = 0
            return

        self._append_conversation(f"> {text}")
        self._live = self._fresh_live_state()
        self._live["active"] = True
        self._live["start_time"] = time.monotonic()
        self._live["current_action"] = "Thinking…"
        self._run_turn_worker(text)

    # ── agent worker ────────────────────────────────────────────────────────

    @work(thread=True, exclusive=True)
    def _run_turn_worker(self, text: str) -> None:
        try:
            self.repl.run_turn(text)
        except TurnCancelled:
            self._events.put({"phase": "turn_interrupted"})
        except Exception as e:
            self._events.put({"phase": "turn_error", "error": str(e)})
        finally:
            self._events.put({"phase": "turn_complete"})
