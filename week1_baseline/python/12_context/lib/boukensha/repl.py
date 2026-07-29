from __future__ import annotations

import os
import socket
import threading
from typing import Any, Callable

from .agent import Agent
from .errors import ApiError, LoopError


class Repl:
    """The interactive session loop.

    It wraps the same primitives as a single run() call, but instead of
    running once it stays alive: it reads a task from the user, runs the
    agent, prints the reply, and loops back to the prompt.

    The Context is shared across every turn so conversation history
    accumulates naturally -- the agent sees the full transcript each time
    it is called.

    Built-in commands (not sent to the agent):
      /help    print the command list
      /clear   wipe conversation history (tools stay registered)
      /compact drop oldest 40% of messages to free context
      /exit    leave the REPL
      /quit    alias for /exit
    """

    PROMPT = "boukensha> "

    HELP = (
        "Commands:\n"
        "  /clear    wipe conversation history (tools stay)\n"
        "  /compact  drop oldest 40% of messages to free context\n"
        "  /exit     leave the REPL\n"
        "  /help     show this message\n"
    )

    def __init__(
        self,
        *,
        context: Any,
        registry: Any,
        builder: Any,
        client: Any,
        logger: Any,
        config_dir: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        version: str | None = None,
        api_key: str | None = None,
        mud: dict[str, Any] | None = None,
        max_iterations: int | None = None,
        max_turn_tokens: int | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        self.context = context
        self.registry = registry
        self.builder = builder
        self.client = client
        self.logger = logger
        self.max_iterations = max_iterations
        self.max_turn_tokens = max_turn_tokens
        self.max_output_tokens = max_output_tokens
        self.config_dir = config_dir
        self.provider = provider
        self.model = model
        self.version = version
        self.api_key = api_key
        self.mud = mud
        self.turn = 0
        self._output_cb: Callable[[str], None] | None = None
        # Python-only addition: replaces Ruby's Thread#raise(Interrupt) with a
        # cooperative flag Agent checks between iterations. See interrupt().
        self._cancel_event = threading.Event()

    # Register a callback that receives every string the REPL would otherwise
    # print to stdout. When set, print() is suppressed entirely and all
    # output is routed through the callback instead. Used by Tui.
    def on_output(self, callback: Callable[[str], None]) -> None:
        self._output_cb = callback

    # Request cancellation of the currently running turn (if any). The turn
    # only actually stops at the next iteration boundary inside Agent.run --
    # see the TurnCancelled/cancel_event design note in agent.py.
    def interrupt(self) -> None:
        self._cancel_event.set()

    # Handle a slash command. Returns "quit", "command", or None (not a
    # command). Output is routed through the registered on_output callback
    # if present.
    def handle_command(self, input_text: str) -> str | None:
        if input_text in ("/exit", "/quit"):
            self._output("Goodbye.")
            return "quit"
        elif input_text == "/help":
            self._output(self.HELP)
            return "command"
        elif input_text == "/clear":
            self.context.clear_messages()
            self.turn = 0
            self._output("(conversation history cleared)")
            return "command"
        elif input_text == "/compact":
            dropped = self.context.compact_messages()
            self._output(f"(compacted context — {dropped} messages dropped)")
            return "command"
        return None

    def run_turn(self, input_text: str) -> None:
        self._cancel_event.clear()
        self.turn += 1
        self.logger.turn(n=self.turn)

        self.context.add_message("user", input_text)

        agent = Agent(
            context=self.context,
            registry=self.registry,
            builder=self.builder,
            client=self.client,
            logger=self.logger,
            max_iterations=self.max_iterations,
            max_turn_tokens=self.max_turn_tokens,
            max_output_tokens=self.max_output_tokens,
            cancel_event=self._cancel_event,
        )
        try:
            result = agent.run()
        except LoopError as e:
            self._output(f"\n[error] {e}")
            return
        except ApiError as e:
            self._output(f"\n[error] API call failed: {e}")
            return

        self._output("")
        self._output(result)

    def start(self) -> None:
        self._output(self.banner())

        while True:
            if not self._output_cb:
                print(self.PROMPT, end="", flush=True)

            try:
                raw = input()
            except EOFError:  # Ctrl-D
                break

            text = raw.strip()
            if not text:
                continue

            result = self.handle_command(text)
            if result == "quit":
                break
            if result:
                continue

            self.run_turn(text)

    def _output(self, text: str) -> None:
        if self._output_cb:
            self._output_cb(str(text))
        else:
            print(text)

    def banner(self) -> str:
        key_status = (
            "✗ API key not set"
            if (not self.api_key or not self.api_key.strip())
            else "✓ API key set"
        )
        provider_line = f"{self.provider or 'default'} ({self.model or 'default'})  {key_status}"
        config_exists = self.config_dir and os.path.isdir(self.config_dir)
        config_line = (
            self.config_dir
            if config_exists
            else f"{self.config_dir or '(default)'}  ✗ directory not found"
        )
        ver = self.version or "?.?.?"
        mud_stat = self._mud_status_string()

        return (
            "\n"
            "╔══════════════════════════════════════╗\n"
            f"║  BOUKENSHA MUD Assistant (v{ver}){' ' * (9 - len(ver))}║\n"
            "╚══════════════════════════════════════╝\n"
            f"  config:    {config_line}\n"
            f"  provider:  {provider_line}\n"
            f"  mud:       {mud_stat}\n"
            "\n"
            "  /clear           reset conversation history\n"
            "  /compact         free context (drop oldest messages)\n"
            "  /exit or /quit    leave the REPL\n"
        )

    # Build the mud status string shown in the banner.
    # Only checks TCP reachability -- the tool session auto-connects at
    # startup (in tools.mud.register), so probing login here would cause a
    # double-login.
    def _mud_status_string(self) -> str:
        if not self.mud:
            return "(not configured)"

        host = self.mud.get("host") or "localhost"
        port = self.mud.get("port") or 4000
        name = self.mud.get("name")

        return f"{host}:{port}  {self._probe_mud(host, port, name)}"

    def _probe_mud(self, host: str, port: int, name: str | None) -> str:
        # TCP reachability only -- the tool session auto-connects at startup,
        # so we don't probe login here (that would cause a double-login on boot).
        try:
            with socket.create_connection((host, port), timeout=3):
                pass
        except OSError:
            return "✗ not reachable"
        except Exception as e:
            return f"✗ probe error: {e}"

        return "(Reachable)" if name and str(name).strip() else "(Reachable, no credentials)"
