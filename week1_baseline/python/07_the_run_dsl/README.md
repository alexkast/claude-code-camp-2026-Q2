# Step 7 — The `boukensha.run` DSL (Python port)

Python port of `week1_baseline/ruby/07_the_run_dsl`. Same behavior, same
shared `.boukensha/` config directory — see the Ruby README for the general
idea (before/after comparison). This file documents the Python specifics:
the real `run()` signature (the Ruby README's own option table is stale —
see below) and how the inline tool-registration DSL was translated.

## What this step adds

A single top-level entry point: `boukensha.run(...)`.

Every previous step required manually creating and wiring together a
`Context`, `Registry`, `Backend`, `PromptBuilder`, `Client`, `Logger`, and
`Agent`. This step hides all of that behind one function call.

## The new primitives

### `boukensha.RunDSL`

A tiny host object exposing only `tool(...)`, forwarding straight to
`Registry.tool(...)`. This keeps the surface intentionally small.

### `boukensha.run(...)`

Accepts keyword arguments describing *what* to do; all plumbing happens
internally.

| Option | Default | Description |
|---|---|---|
| `task` | *(required)* | The user message handed to the agent |
| `system` | task's resolved system prompt | System prompt |
| `model` | task's configured model | Model name |
| `backend` | task's configured provider | `"anthropic"`, `"openai"`, `"gemini"`, `"ollama"`, or `"ollama_cloud"` |
| `api_key` | matching `*_API_KEY` env var | API key for the chosen backend (not needed for `"ollama"`) |
| `ollama_host` | `"http://localhost:11434"` | Ollama base URL |
| `log` | `None` | Optional JSONL path override; by default logs go to `.boukensha/sessions/<session-id>.jsonl` |
| `max_output_tokens` | task's configured value (1024 by default) | Max tokens per API response |
| `setup` | `None` | Optional callback receiving a `RunDSL` to register tools on |

The Ruby README's own option table is stale here too (same recurring
pattern as every prior step): it lists `token_budget: 8192` and
`max_tokens: 1024`, neither of which exist in the real method (the real
optional keyword is `max_output_tokens`, no `token_budget` at all), and says
`backend:` supports only `:anthropic`/`:ollama` when the real code supports
all 5 providers. This table reflects the real signature.

## Inline tool registration: the `setup` callback

Ruby's `Boukensha.run(task: "...") do ... end` uses `instance_eval` so
`self` inside the block becomes a `RunDSL` — Python has no block/
instance_eval equivalent. Instead, `run()` takes an optional
`setup: Callable[[RunDSL], None] | None = None` parameter. `run()` builds
the `Context`/`Registry` internally exactly like Ruby does, then — if
`setup` was given — calls `setup(RunDSL(registry))` before the backend/agent
get built:

```python
def register_tools(dsl):
    dsl.tool(
        "read_file",
        description="Read a file from disk",
        parameters={"path": {"type": "string", "description": "File path"}},
        block=lambda *, path: Path(path).read_text(),
    )

result = boukensha.run(task="Summarise lib/boukensha.py", setup=register_tools)
```

`RunDSL.tool(...)` reuses the exact `name, *, description, parameters=None,
block=None` signature already established for `Registry.tool` since step 2
— no new tool-registration shape was invented. `setup` is genuinely
optional; `boukensha.run(task="...")` with no tools registered at all works
fine.

## Before and after

**Step 5/6 — manual plumbing:**

```python
ctx = Context(task=Player, system="You are a MUD player assistant.")
registry = Registry(ctx)
backend = backends.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], model="claude-haiku-4-5")
builder = PromptBuilder(ctx, backend)
client = Client(builder)
logger = Logger()
agent = Agent(context=ctx, registry=registry, builder=builder, client=client, logger=logger)

registry.tool("read_file", description="Read a file", parameters={"path": {"type": "string"}},
              block=lambda *, path: Path(path).read_text())

ctx.add_message("user", "Read lib/boukensha.py")
agent.run()
```

**Step 7 — just describe what you want:**

```python
def register_tools(dsl):
    dsl.tool("read_file", description="Read a file", parameters={"path": {"type": "string"}},
             block=lambda *, path: Path(path).read_text())

boukensha.run(task="Read lib/boukensha.py", setup=register_tools)
```

## What else changed this step

- `Config.mud_host`/`mud_port`/`mud_username`/`mud_password` — removed in
  step 6, **restored** here unchanged.
- `LoopError` — removed in step 6, **restored** here unchanged.
- `Logger.turn(n=...)` and `Logger.subscribe(callback)` — new this step.
  Both are **dormant**: nothing in `Agent` or `example.py` calls them,
  matching Ruby exactly (confirmed via `grep` against this step's Ruby
  source — neither is referenced anywhere). `subscribe`'s callback receives
  the raw phase-specific event dict, **without** the `session_id`/`at`
  fields that get merged in only for the file-written JSON line.

## Run Example

```bash
./week1_baseline/bin/python/07_the_run_dsl
```

**⚠️ Same safety profile as steps 5–6**: this makes a real, multi-turn call
to the live Anthropic API and writes a real session file to the shared
`.boukensha/sessions/`.

## Setup

```bash
cd week1_baseline/python/07_the_run_dsl
python3 -m venv .venv
./.venv/bin/pip install -r requirements-lock.txt
```
