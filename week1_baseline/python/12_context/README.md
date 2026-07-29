# Step 12 — Context Management (Python port)

Python port of `week1_baseline/ruby/12_context`. Adds real context-window
tracking, colour-coded usage warnings, and automatic/manual compaction so the
agent never silently blows past its context window. Also adds "reasoning"
(extended-thinking) content-block support across all 5 LLM backends
(Anthropic, OpenAI, Gemini, Ollama, OllamaCloud) — including OpenAI's switch
from the Chat Completions API to the Responses API. Version `0.12.0`.

This step also **removes the `Tasks::Base`/`Tasks::Player` abstraction
entirely** — its responsibilities are folded directly into `Config`. There is
no `boukensha.tasks` package anymore.

## What's new

### Accurate context tracking

`Context` now maintains two distinct token counts:

| Attribute | What it measures |
|---|---|
| `context_window` | The model's maximum input token capacity |
| `current_tokens` | Tokens actually used in the most recent API call (`usage.input_tokens`) |

Previously (in the Ruby version's history, before this step) the *output*
token budget was shown as if it were the context limit, and a cumulative
session token sum was shown as usage — growing unbounded even after
`/clear`. Both are fixed here: `Agent` updates `current_tokens` after every
API response, and `Context.clear_messages()`/`compact_messages()` both reset
it, so the TUI/REPL always reflect what the *next* call will actually send.

### Context colour coding

The TUI's progress line colours the context indicator based on how full the
window is:

| Usage | Colour | Meaning |
|---|---|---|
| < 70% | Grey | Normal |
| 70–84% | Yellow | Approaching limit |
| ≥ 85% | Red | Compaction imminent |

A `⚠` symbol also appears in the status bar at 85%+.

### Auto-compaction

At the start of every `Agent.run()` call, if
`current_tokens / context_window >= compaction_threshold` (default `0.85`),
the agent automatically compacts the context before making any API call:

```
[context compacted — 12 messages dropped to free space]
```

`Context.compact_messages()` drops the oldest `ceil(40%)` of messages
(keeping at least 2) and resets `current_tokens` to 0 — the first API call
after compaction reports the true new size.

### `/compact` command

Manual compaction, in both the plain REPL and the TUI:

```
boukensha> /compact
(compacted context — 12 messages dropped)
```

### New `Logger` events

- `compaction(before, dropped, context_window)` → `{"phase": "compaction", ...}`
- `reasoning(text, redacted)` → `{"phase": "reasoning", ...}` — one event per
  reasoning/thinking content block returned by the model.
- `plan(text)` → `{"phase": "plan", ...}` — the preamble text (if any) that
  accompanied a tool-use response.
- `prompt(...)` gains a `context_window` field.

**A real regression, reproduced faithfully (confirmed via diff, not README
drift):** `Logger.response()` no longer takes `task`/`backend` and the whole
cost/provider/model/usage-unit metadata enrichment it used to compute
(`_execution_metadata`, `_estimate_cost`, etc. from the step-10/11 Python
port) is gone from Ruby's step-12 `logger.rb`. This port mirrors that
removal exactly — `"response"` log events are now just
`{phase, text, usage, stop_reason}`.

### `run()`/`repl()` — `context_window` replaces implicit task-based sizing

```python
boukensha.repl(context_window=128_000)  # for a smaller model
```

Defaults to `boukensha.models.context_window(model)` when not given.

### Reasoning content blocks — a normalized cross-backend contract

Every backend's `parse_response()` returns content blocks of 3 possible
types (see `backends/base.py`'s docstring for the full contract):

```python
{"type": "reasoning", "text": "...", "signature": "...", "redacted": False}
{"type": "text", "text": "..."}
{"type": "tool_use", "id": "...", "name": "...", "input": {...}}
```

Handling differs per backend when *rebuilding* an assistant turn for a
subsequent request:

| Backend | Reasoning on rebuild |
|---|---|
| Anthropic | Echoed back exactly (`thinking`/`redacted_thinking`, signature preserved) — required, since the API rejects a modified thinking block on a continued turn |
| OpenAI (Responses API) | Dropped — not needed when `reasoning.effort` is `"none"` |
| Gemini | Echoed back (`thought: true` + `thoughtSignature`), but `thoughtSignature` is only included when present (unlike parsing, which always includes the `signature` key, possibly `None`) |
| Ollama / OllamaCloud | Dropped (falls out naturally — only `text`/`tool_use` blocks are kept when rebuilding) |

### OpenAI backend — migrated to the Responses API

`gpt-5.x` rejects `reasoning_effort` + tools on `/v1/chat/completions`, so
this backend now targets `/v1/responses` instead. Beyond the URL:

- Messages become `input` items; the system prompt becomes a top-level
  `instructions` string (not an `input` item).
- Tool defs are flat (`{"type": "function", "name": ..., ...}` — no
  `function:` wrapper).
- Tool results round-trip via `{"type": "function_call_output", "call_id": ..., "output": ...}`
  items, matched by `call_id` (which is also the `tool_use` block's `"id"`),
  rather than a `{"role": "tool"}` message.
- The request always sends `"reasoning": {"effort": "none"}`.

### `boukensha.models` — a known, faithfully-reproduced discrepancy

```python
from boukensha import models
models.context_window("claude-opus-4-8")  # -> 200_000
models.context_window("gpt-5.5")          # -> 32_000 (the module default)
```

`models.py` is a small, separate model → context-window lookup table (3
Anthropic entries + a `32_000` default) used only to default `context_window`
in `run()`/`repl()` when not passed explicitly. **It is never reconciled
with each backend's own, more detailed `MODELS` table** — e.g. Anthropic's
own backend table says Opus/Sonnet have 1,000,000-token windows, but
`models.context_window()` returns 200,000 for those same ids; OpenAI/
Gemini/Ollama models aren't in this table at all, so they get the 32,000
default regardless of their real (400K–1M+) windows.

This is confirmed, real behavior in the Ruby source — not a Python
translation error — and is reproduced here deliberately rather than fixed,
per this project's standing precedent of porting Ruby's actual behavior
(including its quirks). **If you want accurate auto-compaction/colour-coding
for a non-Anthropic-default model, pass `context_window=` explicitly** (e.g.
`boukensha.run(..., context_window=backend.context_window)` after
constructing the backend, or just a literal value).

### `file_system` tools — `list_directory`/`search_files` disabled

Only `pwd`, `read_file`, `write_file`, `delete_file` are registered now.
`list_directory`/`search_files` are commented out in
`tools/file_system.py` (not deleted) — leftover from when this app was a
general coding harness; the player agent has no use for them yet. Kept in
place so a future step can re-enable them.

### No bundled default system prompt

`prompts/system.md` no longer ships with this package. `Config.system_prompt`
is resolved once at construction: if
`tasks.player.prompt_override.system: true` is set in `settings.yaml`, it
reads `<BOUKENSHA_DIR>/prompts/player/system.md`; otherwise (or as a
fallback) `<BOUKENSHA_DIR>/prompts/system.md`. If neither file exists,
`system_prompt` is `None` — there is no library-bundled fallback.

## Run Example

```sh
cd week1_baseline/python/12_context
python3 -m venv .venv
./.venv/bin/pip install -e .

BOUKENSHA_DIR=~/.boukensha ./.venv/bin/boukensha
```

Or via the repo's bin wrappers:

```sh
./week1_baseline/bin/python/12_context
```

## Setup

```sh
cd week1_baseline/python/12_context
python3 -m venv .venv
./.venv/bin/pip install -e .
```
