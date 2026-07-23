# The Tool Registry (Python port)

Python port of `week1_baseline/ruby/02_the_registry`. Same behavior, same
shared `.boukensha/` config directory — see the Ruby README for full design
rationale. This file documents the Python specifics and the differences
from Ruby worth knowing about.

The Tool Registry is how BOUKENSHA manages what capabilities the agent can use.

It has two jobs:
  1. storing tools
  2. dispatching tools when asked

## New Files

| File | Description |
|---|---|
| `lib/boukensha/registry.py` | The `Registry` class — registers tools and dispatches calls |
| `lib/boukensha/errors.py` | BOUKENSHA-specific error classes |

`config.py`, `tool.py`, `message.py`, `context.py`, and the `tasks/` files
are unchanged from `01_struct_skeleton` — copied verbatim, since the Ruby
sources for this step are byte-identical to step 1's.

## How It Works

The agent NEVER calls a tool directly.
It emits a structured request (name and args) and the Registry looks up the tool and runs it.

```
Agent:    "Hey registry call move with direction='north'"
Registry: "looking up 'move' in the tool table"
Registry: "Found it now calling the block with the provided args"
Registry: "Here's the result"
Agent:    "Thanks buddy"
Registry: "Thats why you pay me the big tokes"
```

## `boukensha.Registry`

| Method | Description |
|---|---|
| `tool(name, *, description, parameters=None, block=None)` | Registers a new tool on the context, returns the `Tool` |
| `dispatch(name, args=None)` | Looks up a tool by name and calls it with the provided args |

### Block passing

Ruby's `Registry#tool` takes the tool implementation as an implicit block
(`registry.tool("move", description: ..., parameters: ...) do |direction:| ... end`).
Python has no implicit block syntax, so the callable is passed as an
explicit `block=` keyword argument in the same call:

```python
registry.tool(
    "move",
    description="Move the player in a direction (north, south, east, west, up, down)",
    parameters={"direction": {"type": "string"}},
    block=lambda *, direction: f"You move {direction} into a torch-lit corridor.",
)
```

## `boukensha.UnknownToolError`

Raised when `dispatch` is called with a name that has no registered tool.
A harness needs explicit error boundaries — an unrecognised tool name should never silently fail.

**Example:**
```
UnknownToolError: No tool registered as 'flee'
```

## Considerations — string keys all the way down

Ruby's `dispatch` has to convert the args hash's string keys to symbols
(`args.transform_keys(&:to_sym)`) before splatting them into a
keyword-argument block, because Ruby block keyword params require symbol
keys — the API returns string-keyed JSON but Ruby blocks expect symbols.

Python has no such distinction: `**kwargs` unpacking already works directly
off a string-keyed dict, so `dispatch` just does `tool.block(**args)` with
no key-conversion step. This whole gotcha simply doesn't exist on the
Python side — a language-level simplification, not a functional change.

## Run Example

```bash
./week1_baseline/bin/python/02_the_registry
```

Expected output (values from your `.boukensha/`):

```
=== BOUKENSHA Step 2: Tool Registry ===

Config:  #<Boukensha::Config dir=/home/andrew/Sites/Claude-Code-Camp/.boukensha tasks=player>
Context: #<Context task=player turns=0 tools=2>
Tools:
  #<Tool name=move description=Move the player in a direction (north, so params=['direction']>
  #<Tool name=shout description=Shout a message so everyone in the zone c params=['message']>

Dispatching 'shout' with message='dragon spotted'...
Result: DRAGON SPOTTED

Dispatching 'move' with direction='north'...
Result: You move north into a torch-lit corridor.

UnknownToolError caught: No tool registered as 'flee'
```

## Setup

```bash
cd week1_baseline/python/02_the_registry
python3 -m venv .venv
./.venv/bin/pip install -r requirements-lock.txt
```
