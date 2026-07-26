# Step 7 — The REPL Loop (Python port)

Python port of `week1_baseline/ruby/08_the_repl_loop`. Same behavior, same
shared `.boukensha/` config directory — see the Ruby README for the general
idea. This file documents the Python specifics and the **real** behavior of
`Repl`/`Logger.turn` (the Ruby README describes both inaccurately — see
below).

## What this step adds

| | `boukensha.run` | `boukensha.repl` |
|---|---|---|
| Entry point | one-shot | interactive |
| Turns | one | many |
| History | discarded | accumulates across turns |
| User interaction | none | stdin prompt |

**⚠️ Genuinely open-ended, unlike prior steps.** `example.py` starts an
interactive session against the live Anthropic API — a human at the
keyboard can drive arbitrarily many real API calls, not just one fixed
task.

## `boukensha.Repl`

The interactive session loop. Built-in commands:

| Command | Effect |
|---|---|
| `/quiet` | Sets a flag claiming to suppress logging (see caveat below) |
| `/loud` | Re-enables the flag |
| `/clear` | Wipe conversation history (tools stay registered) |
| `/help` | Print the command list |
| `/exit` / `/quit` | Leave the REPL |
| Ctrl-D | EOF — leave the REPL |
| Ctrl-C | Interrupt — leave the REPL entirely (not just the current turn) |

### The `/quiet` caveat — reproduced faithfully, not fixed

`/quiet` calls `enable_quiet()` and prints
`"(logging suppressed — type /loud to re-enable)"`; `/loud` calls
`disable_quiet()` claiming to re-enable it. **This has zero actual effect**
— `Logger` never checks `is_quiet()` anywhere before writing an event. This
was confirmed against the real Ruby source (`grep` for `quiet?` across the
whole step turns up only the declaration, never a call site that gates
anything). This is different from other dormant features in this codebase
(`LoopError`, the `quiet!`/`loud!`/`quiet?` methods themselves before this
step) — here the commands are genuinely wired up and do run, they just
don't accomplish what their own printed message claims. Ported exactly as
Ruby has it, not silently fixed.

### `boukensha.repl(...)`

Same signature as `boukensha.run(...)`, minus `task` — register tools via
`setup`, then the REPL loop takes over:

```python
def register_tools(dsl):
    dsl.tool(
        "read_file",
        description="Read a file from disk",
        parameters={"path": {"type": "string", "description": "File path"}},
        block=lambda *, path: Path(path).read_text(),
    )

boukensha.repl(model="claude-haiku-4-5", setup=register_tools)
```

Ctrl-C (`KeyboardInterrupt`) is only handled at the `repl()` level, not
inside `Repl.start()` itself — matching Ruby, where `Interrupt` isn't
rescued inside `Repl#start`/`run_turn` at all. An interrupt at the prompt
or mid-API-call exits the entire REPL, not just the current turn.

## What else changed this step

### `Context.clear_messages()`
Wipes `messages` while keeping `tools`/`system` intact. Used by `/clear`.

### `Agent.run()` — persists the final reply

Before this step, the agent returned the final text without adding it to
`Context.messages`. That was harmless for one-shot `run()` (the context is
discarded anyway), but a REPL needs the full transcript so later turns see
prior exchanges:

```python
# before this step — final text returned but NOT in context
return text

# this step — final text added to context, then returned
self.context.add_message("assistant", text)
return text
```

This fix applies at all 3 places a final reply is produced: the main
completion path, the wind-down call's success path, and its `ApiError`
fallback path.

### `Config`'s 3-tier directory resolution

```
1. BOUKENSHA_DIR environment variable
2. .boukensha/ in the current working directory (new this step)
3. ~/.boukensha (default)
```

### `Client`'s friendlier 401 message

A `401` response now raises
`ApiError("authentication failed (401) — check your API key")` instead of
the generic `"API request failed after N attempts (401): <body>"`. 401
isn't retryable either way — this only changes the final error message.

### `Logger.turn(n=...)` — still just a JSONL event

The Ruby README claims this "prints a `╔══ turn N ══╗` header" to the
console. It doesn't — the real method (unchanged since it was added,
dormant, in step 7) only writes a `{"phase": "turn", "n": n}` JSONL event,
same as every other `Logger` method. `Repl._run_turn` calls it once per
turn purely for the log file, nothing is printed from it.

## Running it

```bash
./week1_baseline/bin/python/08_the_repl_loop
```

The example registers `read_file`/`list_directory` tools scoped to the
**sibling `python/07_the_run_dsl` folder** (not this step's own directory —
it already has source files to read/list, making it a good playground), and
`list_directory` now sorts its output (a change from every prior step's
unsorted listing).

## Setup

```bash
cd week1_baseline/python/08_the_repl_loop
python3 -m venv .venv
./.venv/bin/pip install -r requirements-lock.txt
```
