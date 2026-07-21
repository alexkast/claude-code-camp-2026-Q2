---
name: play-mud
description: Connects to and plays the tbaMUD text game running at localhost:4000 (a CircleMUD-derived MUD; default test account dummy/helloworld) using a persistent session driver instead of ad-hoc telnet scripts. Use this skill whenever the user asks to play, explore, log into, or interact with "the MUD", a telnet/tbaMUD/CircleMUD game, or any localhost:4000 text-adventure session -- including tasks like finding a location or shop, listing what's for sale, fighting a monster, picking up or buying items, checking stats/inventory, leveling up, or just "seeing what's going on in the game." Also reach for this whenever a task needs to drive a long-lived, prompt-based TCP game session where output arrives asynchronously (combat rounds, other players' actions) and login is a multi-step interactive sequence -- that pattern breaks naive single-shot connect-and-quit scripts, which is exactly the failure mode this skill exists to avoid.
---

# Playing the tbaMUD

This skill turns "play the MUD" into a driveable loop instead of a puzzle you
solve from scratch each time. Two things make this MUD hard to drive with
throwaway code: the login is a multi-step interactive sequence (not one
command with flags), and the game is asynchronous -- output can arrive
without you sending anything. `scripts/` handles both of those mechanically,
so you can spend your attention on the actual goal.

## Quick start

```bash
export MUD_USER=dummy
export MUD_PASS=helloworld     # never write this into logs or memory files
SESSION_DIR=.mud-session       # pick a fresh directory per play session

bash scripts/mud_start.sh "$SESSION_DIR"        # connects + logs in, waits for readiness
bash scripts/mud_send.sh  "$SESSION_DIR" "look"  # send one command, get the new output back
bash scripts/mud_send.sh  "$SESSION_DIR" "n"
bash scripts/mud_stop.sh  "$SESSION_DIR"         # end the session when done
```

`mud_start.sh` fails loudly (non-zero exit, log tail printed) if login
doesn't complete in 15 seconds -- read the message rather than retrying
blindly, since it usually means the login sequence didn't match what
`references/protocol.md` describes (e.g. a name that doesn't exist yet).

Optional: pipe a command's output through the parser for structured fields
instead of eyeballing the room text:

```bash
bash scripts/mud_send.sh "$SESSION_DIR" "look" | python3 scripts/mud_parse.py
```

This gives you `room_name`, `exits`, and `vitals` (hp/mana/moves) as JSON.
It's a heuristic shortcut, not a substitute for reading the raw text --
combat, NPC speech, and shop listings won't fit this shape.

## The play loop

Repeat until the goal is met, you're blocked, or your step budget runs out:

1. **Observe** -- read the output from your last `mud_send.sh` call.
2. **Orient** -- update your memory files with what you just learned (see
   below). The `[ Exits: ... ]` line is ground truth for room topology --
   trust it over your own assumptions about the map.
3. **Decide** -- choose one command that advances the goal.
4. **Act** -- send it with `mud_send.sh` and go back to step 1.

Sensible defaults unless the user says otherwise: budget around 50 in-game
commands per goal, flee combat below 30% HP, and stop and report back if you
die, disconnect, or revisit the same room 3 times with no progress -- that
last one usually means the map you've built is wrong, not that you need to
keep trying the same thing.

## Memory

Rewrite these each loop iteration -- assume nothing is remembered between
turns except what's written down. If they don't exist yet in the working
directory's `data/` folder, seed them from the templates in `assets/`:

- **`data/player.md`** -- name, class, level, HP/mana/moves, current room,
  inventory, equipment, goal progress.
- **`data/world.md`** -- the world as a graph: per room, its exits and where
  each leads (`unknown` if unexplored). Never delete a known room, and never
  collapse it into a fixed step-by-step path from one starting point -- if
  it can only answer "how do I get to X" starting from one specific room,
  the map is wrong.
- **`data/journal.md`** -- one entry per run: goal, achieved (yes/no/partial),
  steps used, and friction points tagged `confused` / `blocked` / `bored` /
  `overpowered`, including anything that made the session hard to drive
  mechanically, not just what happened in-game.

Never write the password into any of these files, or into `session.log`.

## When you get stuck

Read `references/protocol.md` first -- it documents the exact login prompts
(including the difference between logging into an *existing* character,
which goes straight from name to `Password:`, and creating a *new* one,
which asks a confirmation question first), the room output format, and why
the game is asynchronous. Most "the MUD isn't responding the way I expect"
problems are answered there rather than by writing a new script.

If you truly need custom logic beyond sending commands and reading text
(e.g. parsing a very unusual output shape), extend `scripts/mud_parse.py`
rather than writing a fresh one-off connection script -- the connection and
login handling in `mud_driver.py` already works and is easy to break by
re-deriving it from scratch.
