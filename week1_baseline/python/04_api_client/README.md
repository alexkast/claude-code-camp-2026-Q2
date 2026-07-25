# The API Client (Python port)

Python port of `week1_baseline/ruby/04_api_client`. Same behavior, same
shared `.boukensha/` config directory — see the Ruby README for full design
rationale. This file documents the Python specifics and two intentional
deviations from Ruby, both confirmed during planning.

The API Client takes the payload assembled by `PromptBuilder` and sends it
to the API. One HTTP POST, one response. No tool loop yet — just proving
the round trip works.

**⚠️ Running the example makes a real network call.** `examples/example.py`
sends one real HTTP POST to the configured provider (Anthropic, per the
current `.boukensha/settings.yaml`) using the real API key in `.env`. This
costs a small amount of real API credits, unlike every prior step's fully
local/deterministic example.

## New Files

| File | Description |
|---|---|
| `lib/boukensha/client.py` | Makes the HTTP request and parses the response |

`context.py`, `message.py`, `tool.py`, `registry.py`, `prompt_builder.py`,
`tasks/player.py`, and all 5 `backends/*.py` files are unchanged from
`03_prompt_builder`.

## Updated Files

| File | Change |
|---|---|
| `lib/boukensha/errors.py` | Added `ApiError` for failed HTTP requests |
| `lib/boukensha/tasks/base.py` | `_fetch` now returns `None` immediately if `settings` isn't a `dict`, instead of raising — this is the fix for the exact crash scenario (a task's settings resolving to `None`) encountered while testing `01_struct_skeleton` |
| `prompts/system.md` | New default prompt text this step (`"You are Boukensha, an autonomous player exploring a CircleMUD world..."`) — not the same text as `00_config`/`03_prompt_builder` |

## Two intentional deviations from Ruby

### 1. Fixed the `PROMPTS_DIR` off-by-one bug

Ruby's `config.rb` in this step computes
`File.expand_path("../../../prompts", __dir__)` — 3 levels up from
`lib/boukensha/` — which resolves to `week1_baseline/ruby/prompts`, a
directory that doesn't exist. It should be 2 levels up, matching
`00_config` and `03_prompt_builder`'s (correct) formula, to reach
`04_api_client/prompts/` where `system.md` actually lives. The practical
effect in Ruby: `Tasks::Base.system_prompt` silently falls back to `None`
(no crash) unless the user's own `.boukensha/prompts/player/system.md`
override is in place.

The Python port fixes this — `config.py` uses the same (correct) 2-levels-up
formula as `00_config`/`03_prompt_builder`, so the shipped default prompt is
actually found.

### 2. HTTP client uses `requests`, not stdlib-only

Ruby's `client.rb` deliberately avoids any HTTP library (stdlib `net/http`
only) — the README calls this out explicitly as intentional, to keep the
HTTP call itself visible rather than hidden behind a library. The Python
port uses the third-party `requests` library instead, for cleaner
retry/exception handling. This is a **new dependency** this step —
`requirements.txt` now includes `requests` alongside `python-dotenv` and
`PyYAML`.

## `boukensha.Client`

| Method | Description |
|---|---|
| `call(*, max_output_tokens=1024)` | POSTs the payload and returns the parsed JSON response |

Retry/backoff behavior (identical constants/formula to Ruby):

- Retries transient network errors (`requests.exceptions.ConnectionError`,
  `Timeout`, `SSLError`) and retryable HTTP status codes
  (`408, 409, 429, 500, 502, 503, 504`).
- Up to `MAX_RETRIES = 3` retries, with exponential backoff:
  `0.5 * 2^(attempt - 1)` seconds.
- Raises `ApiError` on final failure — either transient-error exhaustion or
  a non-2xx response after retries are exhausted.
- Otherwise returns the parsed JSON response body.

Ruby's transient-error list (`EOFError`, `Errno::ECONNRESET`,
`Errno::ECONNREFUSED`, `Net::OpenTimeout`, `Net::ReadTimeout`,
`OpenSSL::SSL::SSLError`, `SocketError`, `Timeout::Error`) maps to just three
Python exception types because `requests`/`urllib3` already collapse
connection-refused/reset/DNS-failure/timeout cases into
`ConnectionError`/`Timeout`/`SSLError`. This is a best-effort equivalent,
not a 1:1 mapping — Ruby's and Python's HTTP exception hierarchies aren't
directly comparable.

## Task Configuration

Unchanged from prior steps:

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
```

## What the Response Looks Like

The raw response shape differs between backends — see the Ruby README for
Anthropic/Ollama examples. When the model wants to call a tool, Anthropic
responds with `stop_reason: "tool_use"` and a `tool_use` content block.
Handling that is step 5 — the Agent Loop.

## Considerations

**The client raises `ApiError` on failure.** A non-2xx response means
something went wrong — bad API key, malformed payload, server error.
BOUKENSHA surfaces this explicitly rather than returning a confusing `None`
or partial response.

**Tool blocks in `example.py` do real filesystem I/O** (`read_file`,
`list_directory`), but are never dispatched in this step — only their
schemas are sent to the API as available tools. The model may ask to call
one (as it did when this port was verified — it requested `list_directory`),
but nothing actually executes it yet.

## Run Example

```bash
./week1_baseline/bin/python/04_api_client
```

Sends one real request to the configured provider and prints the raw JSON
response — this will vary run to run since it's a live model call, unlike
every prior step's deterministic output.

## Setup

```bash
cd week1_baseline/python/04_api_client
python3 -m venv .venv
./.venv/bin/pip install -r requirements-lock.txt
```
