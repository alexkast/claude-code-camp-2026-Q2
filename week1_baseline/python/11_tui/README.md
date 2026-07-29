# Step 11 — A Terminal UI (Python port)

Python port of `week1_baseline/ruby/11_tui`. Boukensha now ships a full
terminal UI on top of the step 10 plain REPL. Ruby builds this on the
[`charm`](https://github.com/charm-ruby/charm) gem (bubbletea + lipgloss +
bubbles); there is no Python equivalent of that specific stack, so this port
uses [Textual](https://textual.textualize.io/) instead — a from-scratch
reimplementation of the same four-zone layout and behavior, not a mechanical
translation. Version `0.11.0`.

The plain REPL from step 10 is still there and can be selected with
`tui=False` or the `--no-tui` CLI flag.

## What's new

### `boukensha.tui.BoukenshaApp`

New class (`textual.app.App` subclass). Wraps a `Repl` instance and replaces
its raw `print()`/`input()` I/O with a structured four-zone display:

```
┌──────────────────────────────────────────────┐
│  conversation viewport (scrollable)           │
├──────────────────────────────────────────────┤
│  ⟳ live progress line (hidden when idle)     │
├──────────────────────────────────────────────┤
│  boukensha> input box                         │
├──────────────────────────────────────────────┤
│  status line (always-on)                      │
└──────────────────────────────────────────────┘
```

Built from Textual's `RichLog` (conversation viewport), `Static` (progress
line), `Input` (entry box), and another `Static` (status line).

The **progress line** shows a spinner, current action, iteration counter
(`n/MAX`), elapsed seconds, token counts (↑ in / ↓ out), and tool call count
while the agent is running. When idle it shows context usage and turn count.

The **status line** always shows: version · model · context tokens used ·
registered tool count · wall-clock time.

**Keyboard shortcuts:**

| Key | Action |
|-----|--------|
| `Enter` | Submit input or slash command |
| `Esc` | Request cancellation of the running agent turn |
| `Ctrl+L` | Clear conversation history |
| `PgUp` / `PgDn` | Scroll conversation viewport |
| `Ctrl+C` / `Ctrl+D` | Quit |

The agent runs on a Textual background worker thread (`@work(thread=True)`)
so the UI stays responsive during long turns.

### `Esc` / turn cancellation — a real behavior difference from Ruby

Ruby's `Esc` handler calls `@turn_thread.raise(Interrupt)`, which can deliver
an async exception into a running thread at (almost) any point, including
mid blocking I/O. Python threads have no safe equivalent of this (there's an
unsafe `ctypes` trick to force-inject an exception into another thread, but
it can corrupt state mid-syscall and isn't appropriate here).

Instead, this port uses **cooperative cancellation**:

- `Agent.__init__` takes an optional `cancel_event: threading.Event | None`.
- `Agent.run()` checks it once per loop iteration boundary (after the
  current model/tool round-trip completes, before starting the next one) and
  raises a new `boukensha.errors.TurnCancelled` if set.
- `Repl` owns a `threading.Event`, cleared at the start of every `run_turn`
  call and passed into the `Agent` it constructs. A new public
  `Repl.interrupt()` method sets it — this is what `Esc` calls instead of
  Ruby's `Thread#raise`.

**Practical effect**: a turn can only be interrupted *between* iterations,
not mid-API-call or mid-tool-call. This is a deliberate, confirmed design
choice, not a bug — see `docs/plans/python_port/11_tui` for the discussion.

### `boukensha.repl()` — new `tui` keyword

```python
boukensha.repl(tui=True)   # default — launches the Textual TUI
boukensha.repl(tui=False)  # falls back to the plain terminal REPL
```

The `--no-tui` CLI flag sets `tui=False` from the command line.

### `Repl` refactored for composability

`Repl` no longer hard-codes `print()`/`input()`. Three methods are public so
`BoukenshaApp` (or any other front-end) can drive it:

| Method | Purpose |
|--------|---------|
| `on_output(callback)` | Route all REPL output through a callback instead of stdout |
| `handle_command(input_text)` | Process a slash command; returns `"quit"`, `"command"`, or `None` |
| `run_turn(input_text)` | Run one agent turn and route the result through `on_output` |
| `interrupt()` | Request cooperative cancellation of the currently running turn |

`banner()`, `logger`, `context`, `model`, and `version` are also public.

### `/quiet` and `/loud` are gone

Ruby drops the `/quiet`/`/loud` REPL commands and the module-level
`Boukensha.quiet!`/`loud!`/`quiet?` entirely in this step (confirmed via
diff against step 10 — a real removal, not documentation drift). The Python
port mirrors this: `enable_quiet`/`disable_quiet`/`is_quiet` are removed from
`_state.py` and no longer exported from `boukensha/__init__.py`.

### `Logger.subscribe`

```python
logger.subscribe(lambda event: ...)
```

Already existed in the step 10 Python port (the Ruby README's claim that
this is new in step 11 is stale — `logger.rb` is byte-identical between
steps 10 and 11). Every structured log event (`"iteration"`, `"tool_call"`,
`"tool_result"`, `"response"`, etc.) is broadcast to all registered
subscribers as well as being written to the JSONL file. `BoukenshaApp` uses
this to update the live progress line in real time without polling.

### Legacy `MUD_NAME` env-var override — now actually wired up

`boukensha_loader.py`'s `main()` now honors `MUD_NAME`/`MUD_HOST`/`MUD_PORT`/
`MUD_PASSWORD` (taking precedence over `settings.yaml`'s `mud:` block when
set), matching Ruby's `boukensha_loader.rb`. This logic already existed in
Ruby step 10 but was missed when step 10's Python port was done; it's
included here since step 11's loader needed touching anyway for `--no-tui`.

### `patches/bubbletea/` — not ported

Ruby's `patches/bubbletea/` is a C-extension patch for a burst-read bug in
the precompiled `bubbletea` gem's native code, plus a workaround note for a
conflict between bubbletea's input reader and `ntcharts`'s Go runtime.
Textual is pure Python — no native extension to patch, and no competing Go
runtime — so this directory has no Python counterpart.

## Run Example

The TUI is interactive, so it's run via the global `boukensha` executable
rather than `examples/example.py` (that file is the step 10 MUD demo,
carried over unchanged — it doesn't exercise the TUI).

```sh
cd week1_baseline/python/11_tui
python3 -m venv .venv
./.venv/bin/pip install -e .

# launches the Textual TUI:
BOUKENSHA_DIR=~/.boukensha ./.venv/bin/boukensha

# plain REPL (no Textual rendering):
./.venv/bin/boukensha --no-tui
```

Or via the repo's bin wrappers:

```sh
./week1_baseline/bin/python/11_tui
```

## Setup

```sh
cd week1_baseline/python/11_tui
python3 -m venv .venv
./.venv/bin/pip install -e .
```
