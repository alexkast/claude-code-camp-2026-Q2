from __future__ import annotations

import os
from typing import Any, Callable

from . import backends
from ._state import config
from .agent import Agent
from .client import Client
from .config import Config
from .context import Context
from .logger import Logger
from .prompt_builder import PromptBuilder
from .registry import Registry
from .repl import Repl
from .tasks.player import Player
from .version import VERSION


class RunDSL:
    """The object passed to run()'s/repl()'s setup callback. Exposes only
    `tool`, keeping the DSL surface intentionally small."""

    def __init__(self, registry: Registry) -> None:
        self.registry = registry

    def tool(
        self,
        name: str,
        *,
        description: str,
        parameters: dict[str, Any] | None = None,
        block: Callable[..., Any] | None = None,
    ) -> Any:
        return self.registry.tool(name, description=description, parameters=parameters, block=block)


# The top-level entry point. Wires together every primitive so the caller
# only has to describe *what* to do, not *how* to plumb it.
#
#   def register_tools(dsl):
#       dsl.tool(
#           "read_file",
#           description="Read a file from disk",
#           parameters={"path": {"type": "string", "description": "File path"}},
#           block=lambda *, path: Path(path).read_text(),
#       )
#
#   result = run(task="Summarise lib/boukensha.py", setup=register_tools)
#
# Options:
#   task:         (required) The user message to hand the agent.
#   system:       System prompt. Defaults to config.system_prompt.
#   model:        Model name. Defaults to config.model.
#   backend:      "anthropic" (default), "openai", "gemini", "ollama", or "ollama_cloud".
#   api_key:      API key for the chosen backend. Defaults to the matching
#                 ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY / OLLAMA_API_KEY
#                 env var (loaded from .boukensha/.env). Not needed for "ollama".
#   ollama_host:  Ollama base URL. Defaults to "http://localhost:11434".
#   log:          Optional JSONL path override. Defaults to .boukensha/sessions/<session-id>.jsonl.
#   max_output_tokens: Per-reply output cap. Defaults to config (1024).
#   setup:        Optional callback receiving a RunDSL to register tools on.
def run(
    *,
    task: str,
    system: str | None = None,
    model: str | None = None,
    backend: str | None = None,
    api_key: str | None = None,
    ollama_host: str = "http://localhost:11434",
    log: str | None = None,
    max_output_tokens: int | None = None,
    setup: Callable[[RunDSL], None] | None = None,
) -> str:
    logger = None
    try:
        cfg = config()  # loads .env; populates os.environ
        task_class = Player
        task_settings = cfg.tasks(task_class.task_name())

        if system is None:
            system = task_class.system_prompt(
                task_settings,
                user_prompts_dir=cfg.user_prompts_dir(),
                default_prompts_dir=Config.PROMPTS_DIR,
            )
        if model is None:
            model = task_class.model(task_settings)
        if backend is None:
            backend = task_class.provider(task_settings)
        if api_key is None:
            api_key = {
                "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
                "openai": os.environ.get("OPENAI_API_KEY"),
                "gemini": os.environ.get("GEMINI_API_KEY"),
                "ollama_cloud": os.environ.get("OLLAMA_API_KEY"),
            }.get(backend)

        ctx = Context(task=task_class, system=system)
        registry = Registry(ctx)

        if setup is not None:
            setup(RunDSL(registry))

        if backend == "anthropic":
            be = backends.Anthropic(api_key=api_key, model=model)
        elif backend == "openai":
            be = backends.OpenAI(api_key=api_key, model=model)
        elif backend == "gemini":
            be = backends.Gemini(api_key=api_key, model=model)
        elif backend == "ollama":
            be = backends.Ollama(host=ollama_host, model=model)
        elif backend == "ollama_cloud":
            be = backends.OllamaCloud(api_key=api_key, model=model)
        else:
            raise ValueError(
                f"Unknown backend {backend!r}. Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'."
            )

        builder = PromptBuilder(ctx, be)
        client = Client(builder)
        effective_max_iterations = task_class.max_iterations(task_settings)
        effective_max_output_tokens = max_output_tokens or task_class.max_output_tokens(task_settings)
        logger = Logger(
            log=log,
            snapshot={
                "task": task_class.task_name(),
                "max_iterations": effective_max_iterations,
                "max_output_tokens": effective_max_output_tokens,
                "model": model,
                "provider": backend,
            },
        )
        agent = Agent(
            context=ctx,
            registry=registry,
            builder=builder,
            client=client,
            logger=logger,
            task_settings=task_settings,
            max_iterations=effective_max_iterations,
            max_output_tokens=effective_max_output_tokens,
        )

        ctx.add_message("user", task)
        return agent.run()
    finally:
        if logger is not None:
            logger.close()


# Interactive REPL: register tools once, then loop -- reading tasks from stdin,
# running the agent, and printing replies -- until the user types /exit or sends EOF.
#
# Conversation history accumulates across every turn so the agent always sees
# the full transcript.
#
# Options are the same as run(), minus `task` (the user supplies tasks
# interactively). system/model/backend/api_key all default to config values.
def repl(
    *,
    system: str | None = None,
    model: str | None = None,
    backend: str | None = None,
    api_key: str | None = None,
    ollama_host: str = "http://localhost:11434",
    log: str | None = None,
    max_output_tokens: int | None = None,
    setup: Callable[[RunDSL], None] | None = None,
) -> None:
    logger = None
    try:
        cfg = config()  # loads .env; populates os.environ
        task_class = Player
        task_settings = cfg.tasks(task_class.task_name())

        if system is None:
            system = task_class.system_prompt(
                task_settings,
                user_prompts_dir=cfg.user_prompts_dir(),
                default_prompts_dir=Config.PROMPTS_DIR,
            )
        if model is None:
            model = task_class.model(task_settings)
        if backend is None:
            backend = task_class.provider(task_settings)
        if api_key is None:
            api_key = {
                "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
                "openai": os.environ.get("OPENAI_API_KEY"),
                "gemini": os.environ.get("GEMINI_API_KEY"),
                "ollama_cloud": os.environ.get("OLLAMA_API_KEY"),
            }.get(backend)

        ctx = Context(task=task_class, system=system)
        registry = Registry(ctx)

        if setup is not None:
            setup(RunDSL(registry))

        if backend == "anthropic":
            be = backends.Anthropic(api_key=api_key, model=model)
        elif backend == "openai":
            be = backends.OpenAI(api_key=api_key, model=model)
        elif backend == "gemini":
            be = backends.Gemini(api_key=api_key, model=model)
        elif backend == "ollama":
            be = backends.Ollama(host=ollama_host, model=model)
        elif backend == "ollama_cloud":
            be = backends.OllamaCloud(api_key=api_key, model=model)
        else:
            raise ValueError(
                f"Unknown backend {backend!r}. Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'."
            )

        builder = PromptBuilder(ctx, be)
        client = Client(builder)
        effective_max_iterations = task_class.max_iterations(task_settings)
        effective_max_output_tokens = max_output_tokens or task_class.max_output_tokens(task_settings)
        logger = Logger(
            log=log,
            snapshot={
                "task": task_class.task_name(),
                "max_iterations": effective_max_iterations,
                "max_output_tokens": effective_max_output_tokens,
                "model": model,
                "provider": backend,
            },
        )

        Repl(
            context=ctx,
            registry=registry,
            builder=builder,
            client=client,
            logger=logger,
            task_settings=task_settings,
            max_iterations=effective_max_iterations,
            max_output_tokens=effective_max_output_tokens,
            config_dir=cfg.dir,
            provider=backend,
            model=model,
            version=VERSION,
            api_key=api_key,
        ).start()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if logger is not None:
            logger.close()
