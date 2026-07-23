# The Prompt Builder (Python port)

Python port of `week1_baseline/ruby/03_prompt_builder`. Same behavior, same
shared `.boukensha/` config directory — see the Ruby README for full design
rationale (motivation for multi-LLM support, per-backend format tables).
This file documents the Python specifics and two intentional deviations
from Ruby, both confirmed during planning.

The Prompt Builder serializes `Context` into the exact format each API
expects. `PromptBuilder` delegates to whichever backend you pass in.
`PromptBuilder` does not call the API — it only prepares the payload.

## New Files

| File | Description |
|---|---|
| `lib/boukensha/prompt_builder.py` | Delegates serialization to the active backend |
| `lib/boukensha/backends/base.py` | Shared backend contract for model validation and model metadata |
| `lib/boukensha/backends/anthropic.py` | Serializes context into the Anthropic API format |
| `lib/boukensha/backends/ollama.py` | Serializes context into the Ollama API format |
| `lib/boukensha/backends/ollama_cloud.py` | Serializes context into the Ollama Cloud API format |
| `lib/boukensha/backends/openai.py` | Serializes context into the OpenAI Chat Completions format |
| `lib/boukensha/backends/gemini.py` | Serializes context into the Gemini `generateContent` format |
| `lib/boukensha/errors.py` | Adds `UnsupportedModelError` alongside `UnknownToolError` |

`context.py`, `message.py`, `tool.py`, `registry.py`, and the `tasks/` files
are unchanged from `02_the_registry`. `config.py` and `prompts/system.md`
are unchanged from `00_config` (this step reintroduces `PROMPTS_DIR`, which
steps 1 and 2 didn't need).

## How It Works

```
Context (Python objects)
        ↓
PromptBuilder
        ↓
Backend (Anthropic, OpenAI, Gemini, or Ollama)
        ↓
API Payload (plain dicts and lists)
        ↓
POST to API
```

## `boukensha.PromptBuilder`

| Method | Description |
|---|---|
| `to_messages()` | Delegates message serialization to the backend |
| `to_tools()` | Delegates tool serialization to the backend |
| `to_api_payload(*, max_output_tokens=1024)` | Assembles the complete payload ready to POST |
| `headers` (property) | Returns the correct headers for the backend |
| `url` (property) | Returns the correct endpoint URL for the backend |

## Two intentional deviations from Ruby

### 1. Fixed a latent arity bug in `to_messages`

Ruby's `PromptBuilder#to_messages` calls `@backend.to_messages(@context.messages)`
(1 argument). But `Ollama`, `OllamaCloud`, and `OpenAI` define
`to_messages(system, messages)` (2 required arguments), while only
`Anthropic` and `Gemini` define `to_messages(messages)` (1 argument).
Calling `builder.to_messages` directly in Ruby would raise an `ArgumentError`
for 3 of the 5 backends. This bug never surfaces in `example.rb`, because it
only calls `to_api_payload` — each backend's own `to_payload` calls its own
`to_messages` internally with the right arity, bypassing `PromptBuilder`'s
broken wrapper entirely.

The Python port fixes this: every backend's `to_messages(system, messages)`
takes a uniform signature. `Anthropic` and `Gemini` simply ignore the
`system` argument when building their message list (they still use
`context.system` separately for the top-level `system`/`systemInstruction`
field in `to_payload`). `PromptBuilder.to_messages()` always calls
`self.backend.to_messages(self.context.system, self.context.messages)`, and
this works identically for all 5 backends — verified directly (not just
through `to_api_payload`).

### 2. Renamed `model_info` classmethod to `model_info_for`

Ruby's `Backends::Base` defines `model_info` twice under one name: a class
method `self.model_info(model)` (MODELS table lookup by name) and an
instance method `model_info` (no args, the cached per-instance hash) — legal
in Ruby because class methods and instance methods are separate namespaces.
Python can't have two same-named methods with different signatures on one
class, so the classmethod is renamed to `model_info_for(model)`. The no-arg
instance accessor keeps the name `model_info`, exposed as a `@property`.

## `boukensha.backends.Base`

| Member | Kind | Description |
|---|---|---|
| `models()` | classmethod | Returns the concrete backend's `MODELS` dict; raises `NotImplementedError` if a subclass didn't define one |
| `model_info_for(model)` | classmethod | Looks up one model's metadata dict by name |
| `validate_model(model)` | classmethod | Coerces to `str`, raises `UnsupportedModelError` if unsupported |
| `model_info` | property | The validated model's cached metadata dict |
| `context_window` | property | The model's known token context window |
| `input_token_cost_per_million` / `output_token_cost_per_million` | property | USD price per million tokens, or `None` if usage-based |
| `usage_unit` | property | `"tokens"`, `"local_compute"`, or `"ollama_cloud_usage"` |
| `usage_level` | property | Ollama Cloud usage tier, `None` if not applicable |
| `estimate_cost(*, input_tokens, output_tokens)` | method | Returns `None` if either per-million cost is `None` |

A backend refuses to initialize with an unknown model, so `settings.yaml`
cannot silently select an unsupported or misspelled model.

The prices in this step are static tutorial data, current as of June 16,
2026, and should be reviewed whenever the selected model set changes.

## Backends

| Backend | Endpoint | Auth |
|---|---|---|
| `Anthropic` | `https://api.anthropic.com/v1/messages` | `ANTHROPIC_API_KEY` |
| `Ollama` | `http://localhost:11434/api/chat` (or `host=`) | none (local) |
| `OllamaCloud` | `https://ollama.com/api/chat` | `OLLAMA_API_KEY` |
| `OpenAI` | `https://api.openai.com/v1/chat/completions` | `OPENAI_API_KEY` |
| `Gemini` | `.../v1beta/models/{model}:generateContent` | `GEMINI_API_KEY` |

### System Prompt

Anthropic and Gemini send the system prompt as a top-level field. Ollama,
OllamaCloud, and OpenAI put it inside the messages array as a `role: system`
message.

### Tool Results

Anthropic wraps tool results in a user message. Ollama/OllamaCloud use
`role: tool` with `tool_name`; OpenAI uses `role: tool` with `tool_call_id`.
Gemini wraps results in a `functionResponse` part on a `user` message.

### Tool Definitions

Anthropic uses `input_schema`. Ollama/OllamaCloud/OpenAI wrap everything in
a `function` envelope with `parameters`. Gemini wraps tools in a
`functionDeclarations` array (an empty list if there are no tools, to avoid
emitting an empty wrapper).

### Message Roles

Anthropic, Ollama, OllamaCloud, and OpenAI all use `assistant` for the
model's turn. Gemini calls it `model`.

## Considerations

**The conversation is stateless.** The model has no memory between turns.
Every API call includes the entire history from the beginning. BOUKENSHA is
responsible for carrying that state.

**Tool results are user messages on Anthropic.** This feels counterintuitive
— the result came from BOUKENSHA, not the human — but it reflects how the
Anthropic API models the conversation. Ollama, OllamaCloud, OpenAI, and
Gemini all handle this with dedicated message/part types instead.

**The agent only sees schemas.** The `description` field on each tool is the
only thing the agent uses to decide which tool to call. The actual callable
never leaves BOUKENSHA.

## Run Example

```bash
./week1_baseline/bin/python/03_prompt_builder
```

Runs against the `.boukensha/settings.yaml` fixture (`provider: anthropic`,
`model: claude-haiku-4-5`), prints a `Config:`/`Provider:`/`Model:` header,
then a pretty-printed JSON payload (via `json.dumps(..., indent=2)` — close
to but not byte-identical to Ruby's `JSON.pretty_generate`, since the two
pretty-printers differ slightly in whitespace conventions).

## Setup

```bash
cd week1_baseline/python/03_prompt_builder
python3 -m venv .venv
./.venv/bin/pip install -r requirements-lock.txt
```
