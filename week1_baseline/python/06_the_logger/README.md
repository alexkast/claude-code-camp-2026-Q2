# Step 6 - The Logger (Python port)

Python port of `week1_baseline/ruby/06_the_logger`. Same behavior, same
shared `.boukensha/` config directory — see the Ruby README for the general
idea. This file documents the Python specifics and the real method
signatures/JSONL shapes (the Ruby README's own method table is slightly
stale — see below).

`boukensha.Logger` records each agent run as structured JSON Lines. It is a
file logger, not user-facing display output — running the example now only
prints a header block and the final response; every turn-by-turn detail
goes to a session log file instead.

**⚠️ Same safety profile as step 5**: `examples/example.py` still runs a
real, multi-turn agent loop against the live Anthropic API. New this step:
it also writes a real JSONL file into the **shared** `.boukensha/sessions/`
directory (used by both Ruby and Python runs — a Ruby-generated sample is
already committed there from an earlier test run).

## Session Logs

Each `Logger` instance creates a session id and writes one log file:

```text
.boukensha/sessions/<session-id>.jsonl
```

Every line is a complete JSON object with `session_id`, `at`, and `phase`
fields, plus phase-specific data.

## New Files

| File | Description |
|---|---|
| `lib/boukensha/logger.py` | The `Logger` class |
| `lib/boukensha/_state.py` | Python-only — see "Global state" below |

`context.py`, `message.py`, `tool.py`, `registry.py`, `client.py`,
`prompt_builder.py`, `tasks/player.py`, `tasks/base.py`, and all
`backends/*.py` files are unchanged from `05_agent_loop`.

## Updated Files

| File | Change |
|---|---|
| `lib/boukensha/config.py` | `mud_host`/`mud_port`/`mud_username`/`mud_password` removed — dead scaffolding, unreferenced anywhere |
| `lib/boukensha/errors.py` | `LoopError` removed (it was already unused/dormant since step 5) |
| `lib/boukensha/agent.py` | Wired to a `Logger` for every phase; tool dispatch is now non-fatal — an exception from a tool is caught, logged with `ok=False`, and fed back to the model as an `"ERROR: ..."` string instead of crashing the loop |

## Global state (`boukensha.enable_debug()`, etc.)

Ruby reopens the `Boukensha` module itself to add `Boukensha.config`,
`Boukensha.quiet!`/`.loud!`/`.quiet?` (currently unused anywhere — fully
dormant), and `Boukensha.debug!`/`.debug?` (used: `Logger.raw` checks it).
Ruby's bang/question-mark method names can't be flattened to the same
Python identifier twice, so these became:

| Ruby | Python |
|---|---|
| `Boukensha.config` | `boukensha.config()` |
| `Boukensha.quiet!` | `boukensha.enable_quiet()` (dormant) |
| `Boukensha.loud!` | `boukensha.disable_quiet()` (dormant) |
| `Boukensha.quiet?` | `boukensha.is_quiet()` (dormant) |
| `Boukensha.debug!` | `boukensha.enable_debug()` |
| `Boukensha.debug?` | `boukensha.is_debug()` |

This state lives in a small internal module, `lib/boukensha/_state.py` (no
Ruby equivalent file). Ruby can define this inline in `boukensha.rb` because
`logger.rb` looks up `Boukensha.debug?` at runtime with no import-time
dependency. In Python, having `logger.py` import back from the package's
own `__init__.py` while `__init__.py` is still executing would be a fragile,
order-dependent circular import. Putting the state in a small leaf module
that both `logger.py` and `__init__.py` (for the public
`boukensha.enable_debug()` re-export) import from independently avoids that
entirely — same public surface, safer Python wiring.

## `boukensha.Logger` (real method signatures)

The Ruby README's own method table is slightly stale (omits `max:` on
`iteration`, `ok:`/`error:` on `tool_result`, and lists a `budget:` param on
`prompt` that doesn't exist in the real code). Here's what the real code
does:

| Method | Phase | Fields logged |
|---|---|---|
| `iteration(*, n, max)` | `iteration` | `n`, `max` |
| `limit_reached(*, kind, n, max)` | `limit_reached` | `kind`, `n`, `max` |
| `turn_end(*, reason, iterations, tokens=None)` | `turn_end` | `reason`, `iterations`, `tokens` (always `null` — `Agent` never passes it) |
| `prompt(*, messages, tools)` | `prompt` | `message_count`, `messages` (serialized `{role, content}`), `tool_count`, `tools` (names) |
| `tool_call(*, name, args)` | `tool_call` | `name`, `args` |
| `tool_result(*, name, result, ok=True, error=None)` | `tool_result` | `name`, `result` (stringified), `ok`, `error` |
| `response(*, text, usage=None, stop_reason=None, task=None, backend=None)` | `response` | `text`, `usage`, `stop_reason`, plus `task`/`provider`/`model`/`usage_unit`/`usage_level`/`input_tokens`/`output_tokens`/`cost_usd` when resolvable (unresolvable fields are omitted, not `null`) |
| `raw(*, data)` | `raw` | `data` — only written when `boukensha.is_debug()` is `True` |

### The `provider` field's `"open_ai"` quirk

`response`'s `provider` field is derived from the backend's class name via
a regex-based CamelCase→snake_case conversion (matching Ruby's own
`gsub(/([a-z\d])([A-Z])/, '\1_\2')`). This produces `"open_ai"` for the
OpenAI backend — not `"openai"` — because `"OpenAI"` has a
lowercase-then-two-uppercase transition (`nA` → `n_A`) that the regex
doesn't special-case. Every other backend converts cleanly (`Anthropic` →
`anthropic`, `Gemini` → `gemini`, `Ollama` → `ollama`, `OllamaCloud` →
`ollama_cloud`). This is a real quirk of Ruby's own conversion, kept
faithfully rather than "fixed" — it's cosmetic (log-field-only) and fixing
it would just diverge from what Ruby actually produces.

## Task Configuration

Unchanged from step 5:

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
    max_iterations: 25
    max_output_tokens: 1024
```

## Default usage

```python
logger = Logger()
agent = Agent(context=ctx, registry=registry, builder=builder, client=client, logger=logger)
```

You can also provide a session id or override the destination directory:

```python
Logger(session_id="manual-session")
Logger(dir="/tmp/boukensha-sessions")
```

For compatibility, `log=` still accepts an explicit file path, but normal
usage should write under `.boukensha/sessions`.

## Debug Events

```python
import boukensha
boukensha.enable_debug()
```

Call this before running the agent to include raw provider responses as
`raw` phase lines in the session log.

## Considerations

**Tool errors are no longer fatal.** `Agent` catches any exception raised
by `Registry.dispatch`, logs a `tool_result` with `ok=False` and the error
message, and feeds `f"ERROR: {type}: {message}"` back to the model as the
tool result — the loop continues instead of crashing.

## Run Example

```bash
./week1_baseline/bin/python/06_the_logger
```

## Setup

```bash
cd week1_baseline/python/06_the_logger
python3 -m venv .venv
./.venv/bin/pip install -r requirements-lock.txt
```
