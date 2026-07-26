from __future__ import annotations

import os
from typing import Any

from ._state import disable_quiet, enable_quiet
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
      /quiet   suppress detailed logging
      /loud    re-enable logging
      /clear   wipe conversation history (tools stay registered)
      /exit    leave the REPL
      /quit    alias for /exit
    """

    PROMPT = "boukensha> "

    HELP = (
        "Commands:\n"
        "  /quiet   suppress logging output\n"
        "  /loud    re-enable logging output\n"
        "  /clear   wipe conversation history (tools stay)\n"
        "  /exit    leave the REPL\n"
        "  /help    show this message\n"
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
        task_settings: dict[str, Any] | None = None,
        max_iterations: int | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        self.context = context
        self.registry = registry
        self.builder = builder
        self.client = client
        self.logger = logger
        self.task_settings = task_settings
        self.max_iterations = max_iterations
        self.max_output_tokens = max_output_tokens
        self.config_dir = config_dir
        self.provider = provider
        self.model = model
        self.version = version
        self.api_key = api_key
        self.turn = 0

    def start(self) -> None:
        print(self._banner())

        while True:
            try:
                raw = input(self.PROMPT)
            except EOFError:  # Ctrl-D
                break

            text = raw.strip()
            if not text:
                continue

            if text in ("/exit", "/quit"):
                print("Goodbye.")
                break
            elif text == "/help":
                print(self.HELP)
                continue
            elif text == "/quiet":
                enable_quiet()
                print("(logging suppressed — type /loud to re-enable)")
                continue
            elif text == "/loud":
                disable_quiet()
                print("(logging enabled)")
                continue
            elif text == "/clear":
                self.context.clear_messages()
                self.turn = 0
                print("(conversation history cleared)")
                continue

            self._run_turn(text)

    def _banner(self) -> str:
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

        return (
            "\n"
            "╔══════════════════════════════════════╗\n"
            f"║  BOUKENSHA MUD Assistant (v{ver}){' ' * (9 - len(ver))}║\n"
            "╚══════════════════════════════════════╝\n"
            f"  config:    {config_line}\n"
            f"  provider:  {provider_line}\n"
            "\n"
            "  /quiet or /loud   toggle logging\n"
            "  /clear           reset conversation history\n"
            "  /exit or /quit    leave the REPL\n"
        )

    def _run_turn(self, input_text: str) -> None:
        self.turn += 1
        self.logger.turn(n=self.turn)

        self.context.add_message("user", input_text)

        agent = Agent(
            context=self.context,
            registry=self.registry,
            builder=self.builder,
            client=self.client,
            logger=self.logger,
            task_settings=self.task_settings,
            max_iterations=self.max_iterations,
            max_output_tokens=self.max_output_tokens,
        )
        try:
            result = agent.run()
        except LoopError as e:
            print(f"\n[error] {e}")
            return
        except ApiError as e:
            print(f"\n[error] API call failed: {e}")
            return

        # Print the final response outside of the logger so it is always visible,
        # even when enable_quiet() is active.
        print()
        print(result)
