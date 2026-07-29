# Step 10 — A Standard Tool Library (Python port)

Python port of `week1_baseline/ruby/10_standard_tool_library`. Adds three
built-in tool libraries that `run()`/`repl()` register automatically:
`boukensha.tools.file_system` (sandboxed file operations),
`boukensha.tools.shell` (command execution), and `boukensha.tools.mud`
(27 CircleMUD gameplay tools). Version `0.10.0`.

## `boukensha.tools.file_system`

Registered automatically when `working_dir` is truthy (default:
`os.getcwd()`). All paths are sandboxed to that root — absolute paths and
`../` escapes return an error string instead of raising.

| Tool | Description |
|---|---|
| `pwd` | Return the working directory |
| `list_directory` | List entries at a path (default `.`) |
| `read_file` | Read a file's full contents |
| `write_file` | Write/overwrite a file, creating parent dirs |
| `delete_file` | Delete a file (not directories) |
| `search_files` | Regex search across files, `path:line:content` format |

Pass `working_dir=False` to opt out entirely.

## `boukensha.tools.shell`

One tool, `run_command` — runs inside the working directory with a
configurable `shell_timeout` (default 30s) and an optional
`allowed_commands` allow-list (checked against the command's first
whitespace-split token; `None` permits everything).

## `boukensha.tools.mud` — an original Python reimplementation

Ruby's version depends on a bespoke gem, `mud_manager`, for the actual
telnet session. That gem isn't pip-installable, so this port includes:

- **`boukensha.mud_session.MudSession`** — a from-scratch telnet client
  (stdlib `socket` + `threading` only, no third-party dependency),
  translated directly from the vendored gem source at
  `week0_explore/mud_manager/lib/mud_manager/session.rb`: background
  reader thread, telnet IAC byte stripping, `open`/`close`/`send_command`/
  `drain`/`read_until`/`read_until_quiet`/`read_until_prompt`, and the
  CircleMUD login dance (username → password → Welcome/Reconnecting/Wrong
  password branching).
- **`boukensha.mud_primitives`** — stateless command builders, translated
  from `week0_explore/mud_manager/lib/mud_manager/primitives.rb`. Each
  function validates enum arguments and returns a `Command` describing the
  literal line to send; no I/O, no game-state awareness.
- **`boukensha.tools.mud.register(...)`** — the 27 gameplay tools
  themselves (connection, perception, movement, combat, communication,
  inventory/equipment, magic, utility), each built on `mud_session` +
  `mud_primitives` — this part is a direct 1:1 port of `tools/mud.rb`.

This is a real, working implementation verified against a mock CircleMUD-style
TCP server (login dance, IAC negotiation stripping, prompt-sentinel
waiting, and full tool registration/dispatch) — not a stub.

Auto-connects at registration time; a failed auto-connect logs a message
and continues rather than raising, matching Ruby.

## New `run()`/`repl()` keyword arguments

| Option | Default | Description |
|---|---|---|
| `working_dir` | `os.getcwd()` | Roots FileSystem/Shell tools here; `False` disables both |
| `allowed_commands` | `None` | Allow-list for `run_command`; `None` = allow all, `[]` = disable |
| `shell_timeout` | `30` | Seconds before `run_command` is killed |
| `mud` | `None` | Dict of `host`/`port`/`name`/`password`; `None` = read from `settings.yaml`'s `mud:` block if `mud_host` is set; `False` = disable entirely |

## REPL banner changes

The banner reverts to (and extends) the step-8 style — ✓/✗ API-key status
and config-directory-exists check are both back (they had been dropped in
step 9's reversion), plus a new `mud:` status line showing a TCP
reachability probe (`(Reachable)` / `(Reachable, no credentials)` /
`✗ not reachable` / `(not configured)`). This probe is a lightweight,
separate raw-socket check — it does not reuse or interfere with the real
`MudSession` the tools use, which auto-connects independently at
registration time.

## Run Example

```bash
./week1_baseline/bin/python/10_standard_tool_library
```

Connects to the MUD configured in `.boukensha/settings.yaml`'s `mud:`
block and asks the agent to look around, check its score, and report exits
— `working_dir=False` since this demo needs no filesystem tools.

## Setup

```bash
cd week1_baseline/python/10_standard_tool_library
python3 -m venv .venv
./.venv/bin/pip install -e .
```
