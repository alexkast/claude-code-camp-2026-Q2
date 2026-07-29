from __future__ import annotations

from typing import Any

from .base import Base


class Ollama(Base):
    MODELS: dict[str, dict[str, Any]] = {
        "gemma4:e4b": {
            "context_window": 128_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
    }

    def __init__(self, *, host: str = "http://localhost:11434", model: str) -> None:
        super().__init__()
        self._host = host
        self._configure_model(model)

    def to_messages(self, system: str | None, messages: list[Any]) -> list[dict[str, Any]]:
        system_message = [{"role": "system", "content": system}]
        conversation = []
        for msg in messages:
            if msg.role == "tool_result":
                conversation.append(
                    {"role": "tool", "tool_name": msg.tool_use_id, "content": msg.content}
                )
            elif msg.role == "assistant":
                conversation.append(self._assistant_message(msg.content))
            else:
                conversation.append({"role": msg.role, "content": msg.content})
        return system_message + conversation

    def to_tools(self, tools: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys()),
                    },
                },
            }
            for tool in tools.values()
        ]

    def to_payload(
        self, context: Any, *, max_output_tokens: int = 1024, tools: list[Any] | None = None
    ) -> dict[str, Any]:
        return {
            "model": self.model,
            "stream": False,
            "messages": self.to_messages(context.system, context.messages),
            "tools": self.to_tools(context.tools) if tools is None else tools,
            "think": False,
        }

    @property
    def headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    @property
    def url(self) -> str:
        return f"{self._host}/api/chat"

    # Normalizes an Ollama /api/chat response into the common shape:
    #   {"stop_reason": "tool_use" | "end_turn",
    #    "content": [{"type": "text", "text": ...} | {"type": "tool_use", "id": ..., "name": ..., "input": ...}]}
    #
    # Ollama doesn't assign call ids, so the function name is reused as the
    # id (Ollama also matches tool results back to a call by name).
    def parse_response(self, response: dict[str, Any]) -> dict[str, Any]:
        message = response.get("message") or {}
        tool_calls = message.get("tool_calls") or []

        content: list[dict[str, Any]] = []
        if message.get("thinking"):
            content.append({"type": "reasoning", "text": message["thinking"]})
        if message.get("content"):
            content.append({"type": "text", "text": message["content"]})

        for tc in tool_calls:
            fn = tc.get("function") or {}
            content.append(
                {
                    "type": "tool_use",
                    "id": fn.get("name"),
                    "name": fn.get("name"),
                    "input": fn.get("arguments") or {},
                }
            )

        return {"stop_reason": "end_turn" if not tool_calls else "tool_use", "content": content}

    # Rebuilds an Ollama assistant message from normalized content blocks
    # (the inverse of parse_response). Text-only turns are stored as a bare
    # string, so wrap it back into a single text block before filtering.
    # Reasoning blocks are dropped -- they simply aren't text or tool_use.
    def _assistant_message(self, content: Any) -> dict[str, Any]:
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content

        text_blocks = [b for b in blocks if b["type"] == "text"]
        tool_blocks = [b for b in blocks if b["type"] == "tool_use"]

        message: dict[str, Any] = {
            "role": "assistant",
            "content": "".join(b["text"] for b in text_blocks),
        }
        if tool_blocks:
            message["tool_calls"] = [
                {"function": {"name": b["name"], "arguments": b["input"]}} for b in tool_blocks
            ]
        return message
