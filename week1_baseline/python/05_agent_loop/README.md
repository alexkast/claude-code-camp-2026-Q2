# The Agent Loop (Python port)

Python port of `week1_baseline/ruby/05_agent_loop`. Same behavior, same
shared `.boukensha/` config directory — see the Ruby README for full design
rationale. This file documents the Python specifics and notes worth knowing.

The Agent Loop is the heart of BOUKENSHA. Everything built before this — the
structs, the registry, the prompt builder, the client — was setup. The loop
is where the agent actually does work.

**⚠️ Running the example runs a real, multi-turn agent loop.** Unlike step
4's single request, `examples/example.py` can make several real billed
round-trips to the live Anthropic API (bounded by `max_iterations`, default
25, but realistically 1-3 for the sample task), and dispatches real
`read_file`/`list_directory` tools scoped to this directory.

## New Files

| File | Description |
|---|---|
| `lib/boukensha/agent.py` | The agent loop — sends requests, dispatches tools, and knows when to stop |

`context.py`, `message.py`, `tool.py`, `registry.py`, `tasks/player.py`,
`config.py`, and `backends/base.py` are unchanged from `04_api_client`.

## Updated Files

| File | Change |
|---|---|
| `lib/boukensha/errors.py` | Added `LoopError` — declared but **not currently raised anywhere** (matches Ruby: reserved for a future step) |
| `lib/boukensha/tasks/base.py` | Added `max_iterations(settings)`/`max_output_tokens(settings)`, backed by `DEFAULT_MAX_ITERATIONS = 25`/`DEFAULT_MAX_OUTPUT_TOKENS = 1024` |
| `lib/boukensha/prompt_builder.py` | `to_api_payload` gains a `tools=` passthrough; added `parse_response(response)` delegating to the backend |
| `lib/boukensha/client.py` | `call` gains a `tools=` passthrough to `to_api_payload` |
| `lib/boukensha/backends/*.py` | Each gains `parse_response` (raw response → normalized shape) and `tools=` passthrough on `to_payload`; all but Anthropic also gain a private `_assistant_message`/`_assistant_parts` (the inverse of `parse_response`, for replaying history) |

## How It Works

```
send messages to API
        ↓
stop_reason == "tool_use"?
    yes → extract tool calls
        → dispatch each tool via Registry
        → inject results as tool_result messages
        → go back to top
    no  → return final text response
```

## `boukensha.Agent`

| Method | Description |
|---|---|
| `run()` | Starts the loop and returns the final text response when the agent is done |

## Every Backend Speaks the Same Normalized Shape

Five providers means five different response formats. Rather than teach
`Agent` about each of these, every backend implements `parse_response`,
converting its raw response into one common shape:

```python
{
    "stop_reason": "tool_use" | "end_turn",
    "content": [
        {"type": "text", "text": "..."},
        {"type": "tool_use", "id": "...", "name": "...", "input": {...}},
    ],
}
```

`Agent` only ever sees this shape via `self.builder.parse_response(response)`
and never inspects a raw provider response.

The conversion also runs in reverse: when history is replayed on the next
request, Ollama, OllamaCloud, OpenAI, and Gemini each rebuild a
provider-specific assistant message from the normalized content blocks via
a private `_assistant_message`/`_assistant_parts` method. Anthropic's
`content` array doubles as both the normalized shape and the wire format, so
it needs no extra conversion.

**Tool call IDs aren't universal.** Anthropic and OpenAI assign every tool
call a unique id, echoed back in the `tool_result`. Ollama, OllamaCloud, and
Gemini don't assign call ids at all — those backends reuse the tool's
**name** as its id and match the `tool_result` back to the call by name.

**OpenAI is the only backend that round-trips tool arguments through a JSON
string.** Its wire format encodes `function.arguments` as a JSON string,
which `parse_response` decodes into a dict for the normalized `input` field,
and `_assistant_message` re-encodes back to a JSON string
(`json.dumps(...)`) when rebuilding history. Ollama/OllamaCloud pass
`arguments` as a native dict both ways — no JSON-string step involved.

## `tools=` sentinel semantics

`None` (the default) means "let the backend build tools from
`context.tools`"; an explicit value — including `[]` — means "use exactly
this, don't regenerate." This is how the wind-down call disables tools
entirely (`client.call(tools=[], ...)`) without needing a separate code
path.

## Task Configuration

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

`max_iterations` controls model round-trips per turn before wind-down;
`max_output_tokens` is passed to each model reply. The current
`.boukensha/settings.yaml` doesn't set either key, so both fall back to
their `DEFAULT_*` constants.

## Considerations

**The assistant message must be stored before the tool result.** The
Anthropic API requires the assistant's tool_use block to appear in the
message history before its corresponding tool_result — get the order wrong
and the API rejects the request. `_handle_tool_calls` stores the assistant
message first, then dispatches and stores each result.

**The model can call multiple tools in one turn.** The loop iterates over
all tool_use blocks in a single response before making the next API call.

**`max_iterations` is a turn ceiling, not a hard stop.** A poorly prompted
agent can loop forever if the model keeps calling tools. BOUKENSHA stops
starting new work iterations after the ceiling and makes one short wrap-up
call with tools disabled — this keeps the turn bounded while still returning
a useful final response. If that wind-down call itself fails (`ApiError`),
a deterministic fallback message is returned instead.

**The agent has no way to stop itself.** The model signals it's done via
`stop_reason: "end_turn"`. BOUKENSHA watches for that and exits the loop —
the agent never decides unilaterally to stop.

**`example.py`'s directory listing will differ from Ruby's sample
transcript** — this port's `05_agent_loop/` directory has more entries than
Ruby's (`.venv/`, `requirements.txt`, `requirements-lock.txt`, `__init__.py`
files, etc.), so `list_directory` may return a longer listing than Ruby's
`"README.md, examples, lib"` sample. Expected, not a bug.

## Run Example

```bash
./week1_baseline/bin/python/05_agent_loop
```

## Setup

```bash
cd week1_baseline/python/05_agent_loop
python3 -m venv .venv
./.venv/bin/pip install -r requirements-lock.txt
```
