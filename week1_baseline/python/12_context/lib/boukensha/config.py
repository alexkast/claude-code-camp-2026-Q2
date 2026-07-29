from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class Config:
    # The .boukensha config directory is resolved in this order:
    #   1. BOUKENSHA_DIR environment variable (set before loading .env)
    #   2. ~/.boukensha  (default)
    DEFAULT_DIR: str = str(Path.home() / ".boukensha")

    def __init__(self) -> None:
        self.dir: str = self._resolve_dir()
        self._load_env()
        self.settings: dict[str, Any] = self._load_settings()
        self.system_prompt: str | None = self._load_system_prompt()

    # ---------- provider --------------------------------------------------

    def provider_type(self) -> str:
        return self.dig("tasks", "player", "provider") or "anthropic"

    def model(self) -> str:
        return self.dig("tasks", "player", "model") or "claude-haiku-4-5"

    # ---------- MUD connection --------------------------------------------

    def mud_host(self) -> str:
        return self.dig("mud", "host") or "localhost"

    def mud_port(self) -> int:
        return self.dig("mud", "port") or 4000

    def mud_username(self) -> str | None:
        return self.dig("mud", "username")

    def mud_password(self) -> str | None:
        return self.dig("mud", "password")

    # ---------- agent limits ----------------------------------------------
    # Static per-turn circuit breakers, read where the agent is constructed.
    # A value of 0 or None means "disabled" (no ceiling) -- useful for debugging.

    def agent_max_iterations(self) -> int:
        value = self.dig("agent", "max_iterations")
        return 25 if value is None else int(value)

    def agent_max_output_tokens(self) -> int:
        value = self.dig("agent", "max_output_tokens")
        return 1024 if value is None else int(value)

    def agent_max_turn_tokens(self) -> int:
        value = self.dig("agent", "max_turn_tokens")
        return 60_000 if value is None else int(value)

    def agent_compaction_threshold(self) -> float:
        value = self.dig("agent", "compaction_threshold")
        return 0.85 if value is None else float(value)

    # ---------- low-level helpers -----------------------------------------

    # Fetch a nested key path from settings, e.g. dig("mud", "host")
    def dig(self, *keys: str) -> Any:
        node: Any = self.settings
        for key in keys:
            if isinstance(node, dict):
                node = node.get(key)
            else:
                return None
        return node

    def __str__(self) -> str:
        return f"#<Boukensha::Config dir={self.dir} provider={self.provider_type()} model={self.model()}>"

    def __repr__(self) -> str:
        return str(self)

    def _resolve_dir(self) -> str:
        raw = os.environ.get("BOUKENSHA_DIR") or self.DEFAULT_DIR
        return str(Path(raw).expanduser().resolve())

    def _load_env(self) -> None:
        env_file = Path(self.dir) / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    def _load_settings(self) -> dict[str, Any]:
        settings_file = Path(self.dir) / "settings.yaml"
        if settings_file.exists():
            return yaml.safe_load(settings_file.read_text()) or {}
        return {}

    # Resolves the system prompt. When the player task opts into a prompt
    # override (tasks.player.prompt_override.system: true), the task-scoped
    # file prompts/player/system.md wins; otherwise (and as a fallback) the
    # flat prompts/system.md is used. Returns None when neither exists --
    # there is no bundled default shipped with the library.
    def _load_system_prompt(self) -> str | None:
        if self.dig("tasks", "player", "prompt_override", "system") is True:
            task_file = Path(self.dir) / "prompts" / "player" / "system.md"
            if task_file.exists():
                return task_file.read_text().strip()

        system_file = Path(self.dir) / "prompts" / "system.md"
        return system_file.read_text().strip() if system_file.exists() else None
