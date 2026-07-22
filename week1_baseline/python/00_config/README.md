# 00 · Configuration (Python port)

Python port of `week1_baseline/ruby/00_config`. Same behavior, same
`.boukensha/` config directory, same `settings.yaml` schema — see the Ruby
README for the full design rationale. This file only documents the Python
specifics and the one intentional deviation from the Ruby version.

## Design Considerations

Kept close to the Ruby version's minimal-dependency philosophy: only two
external packages are used —`python-dotenv` (equivalent of the `dotenv` gem)
and `PyYAML` (the standard library has no YAML parser, and `settings.yaml`'s
format is shared with the Ruby side, so this is the one dependency Python
needs that Ruby didn't).

Code is a literal, class-based mirror of the Ruby design (`Config`,
`Tasks.Base`, `Tasks.Player` as classes with classmethods/staticmethods, not
a Pythonic functions/dataclasses redesign) so the two implementations stay
easy to compare step-by-step as later steps are ported.

Targets Python 3.11+.

## Code Changes

| File | Purpose |
|------|---------|
| `lib/boukensha/config.py` | `Config` class |
| `lib/boukensha/tasks/base.py` | abstract `Base` task (provider/model + prompt resolution) |
| `lib/boukensha/tasks/player.py` | concrete `Player(Base)` (the main loop) |
| `lib/boukensha/__init__.py` | top-level package exports |
| `prompts/system.md` | default system prompt shipped with the library |
| `examples/example.py` | runnable smoke-test |

---

## One intentional deviation from Ruby: string-only keys

Ruby's `dig`/`fetch` accept both string and symbol hash keys
(`node[key.to_s] || node[key.to_sym]`) because `settings.yaml` loads as
string keys but Ruby callers pass symbols (`:player`, `:mud`). Python has no
symbol/string duality, so `Config#tasks` and `Config#dig` take plain strings
throughout:

```python
config.tasks("player")   # not config.tasks(:player) — Python has no symbols
config.dig("mud", "host")
```

Everything else — directory resolution, `settings.yaml` schema, prompt
override rules, MUD connection accessors — behaves identically to Ruby.

## Config directory resolution

Same as Ruby — the class looks for a `.boukensha/` directory in this order:

1. **`BOUKENSHA_DIR` env var** — set this to point at any directory you like.
2. **`~/.boukensha`** — the default location for a real install.

## Config directory structure

```
.boukensha/
  .env                 # stores credentials eg. LLMs APIs (never committed to repo)
  settings.yaml        # all non-secret settings
  prompts/
    <task>/
      system.md        # per-task override for the default system prompt (optional)
```

This directory is shared with the Ruby version — both runtimes read the
same `.boukensha/`.

## Tasks

`Tasks.Base` is an abstract stateless class. All behavior is expressed as
classmethods that accept a `settings` dict — no instances are created.
Concrete subclasses define `.task_name()`. For now only `Tasks.Player`
exists.

```python
from boukensha import Config, Player

config = Config()
player_settings = config.tasks("player")

Player.provider(player_settings)
Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir(),
    default_prompts_dir=Config.PROMPTS_DIR,
)
```

## System prompt resolution

Per task, `Player.system_prompt` is resolved in this order:

1. **`.boukensha/prompts/<task>/system.md`** — used when the task's
   `prompt_override.system` is `true` and the file exists.
2. **`prompts/system.md`** — the default system prompt shipped with the library.

## Configuration Schema

Same schema as Ruby (see `../ruby/00_config/README.md`):

```yaml
tasks:
  player:
    provider: anthropic        # provider name (string)
    model: claude-haiku-4-5
    prompt_override:
      system: true
mud:
  host: localhost
  port: 4000
  username: dummy
  password: helloworld
```

## Setup

```bash
cd week1_baseline/python/00_config
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

`requirements.txt` lists unpinned dependencies (like Ruby's `Gemfile`).
`requirements-lock.txt` is the pinned, `pip freeze`-generated equivalent of
`Gemfile.lock` — install from it instead for reproducible versions:

```bash
./.venv/bin/pip install -r requirements-lock.txt
```

## Run Example

```bash
./week1_baseline/bin/python/00_config
```

Expected output (values from your `.boukensha/`):

```
=== Boukensha Step 0: Configuration ===

Config dir:     /home/andrew/Sites/Claude-Code-Camp/.boukensha
Tasks:          player

-- player task --
Provider:       anthropic
Model:          claude-haiku-4-5
Prompt override?true
System prompt:  You are a MUD player assistant. Use the tools available to y...

MUD host:       localhost:4000
MUD user:       dummy

API key set?    true

#<Boukensha::Config dir=/home/andrew/Sites/Claude-Code-Camp/.boukensha tasks=player>
```
