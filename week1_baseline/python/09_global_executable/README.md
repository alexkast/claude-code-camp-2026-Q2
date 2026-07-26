# Step 8 — Global Executable (Python port)

Python port of `week1_baseline/ruby/09_global_executable`. Ruby packages
BOUKENSHA as a RubyGem so `gem install` puts a `boukensha` command on
`$PATH`. This port does the Python-native equivalent: a `pyproject.toml`
with a `console_scripts` entry point, so `pip install -e .` gives a real
`boukensha` command — the first step in this whole port to use real Python
packaging instead of the bare `lib/` + `sys.path` convention every prior
step used.

## Install

```bash
cd week1_baseline/python/09_global_executable
python3 -m venv .venv
./.venv/bin/pip install -e .
```

After that, `./.venv/bin/boukensha` works — "global" here means global
within this step's own virtualenv, not literally system-wide (mirrors
testing a gem inside a clean Bundler environment, not
`gem install --user-install` against your real system).

## Switching steps with `BOUKENSHA_PATH`

The loader (`lib/boukensha_loader.py`) resolves which step's code to run,
in this order:

| Priority | Source | Example |
|---|---|---|
| 1 | `BOUKENSHA_PATH` env var | `BOUKENSHA_PATH=~/week1_baseline/python/08_the_repl_loop ./.venv/bin/boukensha` |
| 2 | `~/.boukensharc` file | `echo ~/week1_baseline/python/08_the_repl_loop > ~/.boukensharc` |
| 3 | Bundled default (this step's own `lib/boukensha/`) | just run `./.venv/bin/boukensha` |

`BOUKENSHA_PATH` must point at a step folder containing `lib/boukensha/__init__.py`.

```bash
# a step that supports the REPL (added in 08_the_repl_loop)
BOUKENSHA_PATH=~/week1_baseline/python/08_the_repl_loop ./.venv/bin/boukensha

# a step that doesn't have repl() yet — loader tells you how to run it instead
BOUKENSHA_PATH=~/week1_baseline/python/04_api_client ./.venv/bin/boukensha
# => boukensha: the step at .../04_api_client does not support the interactive REPL
#    Run its examples directly, e.g.: python .../04_api_client/examples/example.py
```

## Debug mode

```bash
BOUKENSHA_DEBUG=1 ./.venv/bin/boukensha
# => [boukensha] loading from: /path/to/step
```

## The key idea

The package is just a **wrapper and a default**. All the teaching material
stays in the numbered step folders exactly as it was — the loader doesn't
copy or symlink anything, it just knows where to look.

## How the loader avoids importing the wrong `boukensha`

This package's own bundled `lib/boukensha/` gets `pip install -e .`'d under
the name `boukensha` — the same name every other step's package also uses.
A naive `sys.path.insert(0, target_lib_dir); import boukensha` risks
resolving to *this* package's editable install instead of whichever step
`BOUKENSHA_PATH` actually points at. To avoid that ambiguity, the loader
uses `importlib.util.spec_from_file_location` to load the target step's
`__init__.py` explicitly, registering it in `sys.modules["boukensha"]`
*before* executing it (so the target package's own internal relative
imports, like `from .config import Config`, resolve against the right
directory). Verified directly: pointing `BOUKENSHA_PATH` at
`08_the_repl_loop` boots that step's actual code (its `v0.8.0` banner,
which includes a ✓/✗ API-key-status line this step's own bundled banner
does not have — see below), not silently falling back to the bundled
package of the same name.

## Reversions from step 8 — reproduced exactly, not fixed

This step's Ruby source reverts two step-8 improvements without
explanation, and this port matches that faithfully rather than
"helpfully" restoring them:

- **`Config`'s directory resolution is back to 2-tier** (`BOUKENSHA_DIR` env
  var → `~/.boukensha`) — the CWD-`.boukensha/` lookup added in step 8 is
  gone.
- **`Client`'s friendlier 401 message is gone** — a 401 response now raises
  the same generic `"API request failed after N attempts (401): <body>"` as
  any other non-2xx status.
- **The REPL banner drops its ✓/✗ API-key-status line** — it's back to
  plain `config:`/`provider:`/`model:` lines showing the raw value or
  `"(default)"`, with no key-presence check at all.

## The `prompts/system.md` packaging gap — also mirrored, not fixed

The Ruby gemspec's `spec.files` only globs `lib/**/*.rb` + `bin/boukensha` —
`prompts/system.md` isn't included in the packaged gem at all, and the
gemspec's comment claims "ships no external dependencies" even though
`config.rb` requires the (non-stdlib) `dotenv` gem, undeclared.

This port's `pyproject.toml` mirrors the `prompts/system.md` omission
(it's not declared as package data) but **does** correctly declare its real
dependencies (`python-dotenv`, `PyYAML`, `requests`) rather than reproduce
that specific gemspec gap too — declaring your actual runtime dependencies
isn't a "reversion to reproduce," it's just correct packaging.

The `prompts/system.md` gap only manifests under a **real** build
(`python -m build` + installing the resulting wheel) — an **editable**
install (`pip install -e .`, what this README recommends) never copies
files, so `Config.PROMPTS_DIR` still finds the real file in the source tree
regardless of the packaging metadata gap.

## No `examples/` directory this step

Matches Ruby exactly — this step doesn't ship a runnable example script;
the "example" *is* installing and running the `boukensha` command itself.
(Ruby's own `bin/09_global_executable` wrapper is actually broken — it
references a nonexistent `examples/example.rb` — confirming this step was
never meant to be run via the usual per-step wrapper convention.)
