# Explore Agent Architectures

It is often hard for tech professionals to choose the right agent solution, because many
solutions look like they do the same job.

In this document, we test different agent architectures to find the best one for our
agent task.

We use the same simple goal every time, so we can compare the architectures fairly:

> "Find the bakery and list the menu."

The world is a tbaMUD (a text-based game similar to CircleMUD) running on
`localhost:4000`. It is a long, live connection over TCP. Messages from the game can
arrive at any time, and logging in needs several steps, not just one command.

## 1. An agent file with referenced files eg. CLAUDE.md, @data/*.md

In this setup, we use one "agent file" (`CLAUDE.md`) together with simple markdown files
for memory (`player.md`, `world.md`, `journal.md`). The agent rewrites these files every
time it repeats its loop. We started with the smallest model and only moved to a bigger
one if needed.

### Technical Observations

**Haiku 4.5 — failed.** Haiku never reached the bakery. Instead of controlling the
session step by step, it kept writing small, throwaway Python and telnet scripts. It also
misunderstood the login. The user `dummy` is an *existing* character, so the game goes
straight from the name to the `Password:` prompt. Haiku wrongly expected a "Y/N"
confirmation step, which is only used when creating a *new* character. This created
several extra, unwanted characters. Haiku also went off task — for example, it tried to
read the `data` folder as if it were a single file.

**Opus 4.8 — succeeded in about 6 minutes, using 5 in-game commands.** Opus correctly
understood that `dummy` is an existing character, which fixed the login problem right
away. It then built a small background program to manage the connection: it kept the
socket open, sent one command at a time through a FIFO, and saved all game output to a
log file. This matched the intended loop of observe → think → decide → act much better.
The path it found was:
`Temple Of Midgaard → d → Temple Square → s → Market Square → w → Main Street → n → The Bakery`.
The menu was: danish pastry (7 coins), bread (14 coins), waybread (73 coins), all in
unlimited supply. Opus also updated the memory files and never wrote the password into
any log.

### Technical Conclusions

The choice of model made a big difference. With the same agent file and the same memory
design, Haiku failed and Opus succeeded. This shows that this architecture depends a lot
on how capable the model is, which is a risk if we want to use cheaper models later. The
login process itself is always the same, so it is better to use a script that already
knows how to log in, instead of relying on a smarter prompt. The main problem with the
weaker model was that it went off task and kept rewriting fragile connection scripts. The
stronger model also wrote code, but it wrote the *right kind* of code: one reusable driver
instead of many one-off scripts.

So this architecture only partly works. It can succeed, but only with a strong (and more
expensive) model, and only after the agent solves the connection and login problem on its
own. This is a good reason to build our own small MUD SDK — ideally as an MCP server — so
the model does not need to solve the connection problem again every time. Plain markdown
memory worked fine for one short goal, but it will probably not scale well as the world
and player state grow.

## 2. Agent Skills driven by main agent eg. ~/skills

Here we packaged the same task as a Claude Code Skill called `play-mud` (built with the
Anthropic skill-creator) and called it directly from the main agent using `/play-mud` —
no subagent was used. The skill includes a working session driver
(`mud_driver.py`, `mud_start.sh`, `mud_send.sh`, `mud_stop.sh`), a reference document
about the login process, and memory templates that create
`data/player.md`, `data/world.md`, and `data/journal.md`. The file `SKILL.md` also
describes the play loop and clear stop rules (a budget of about 50 commands, flee if HP
drops below 30%, and stop after visiting the same room 3 times without progress). We used
the same session across four different goals to see how the skill behaves over several
turns, not just one.

### Technical Observations

**Sonnet 5 (main agent, no subagent) — succeeded on the main goal on the first try.**

- The login worked without any problems. The driver already knows the difference between
  an existing character and a new one, so the login mistake we saw with Haiku in section 1
  could not happen here. The tooling removed this problem, not a smarter model.
- The goal "find the bakery and list the menu" succeeded twice. The first time, the
  character started near the bakery by luck (3 commands). The second time, the character
  started in a different room (The Pet Shop), and the agent used the saved `world.md` map
  to find the way in 5 commands, without needing the route explained again. This matches
  the goal in `SKILL.md`: build a real map, not just a fixed list of steps.
- A harder, open-ended goal ("go to The Statue's Room") was **not** completed. The agent
  explored about 50 commands worth of the map but never found a room with that exact
  name. It then stopped and reported back, as the skill's rules say, instead of wandering
  around without direction. This is exactly the behavior that was missing from the weaker
  model in section 1.
- One small problem: there was an old `.mud-session` folder left over from a previous,
  already-closed process. The agent had to notice this and clean it up manually, because
  `mud_start.sh` does not check whether the old process is still running.
- The memory files worked as planned. `world.md` grew into a real map of rooms and exits,
  `player.md` tracked progress toward each goal, and `journal.md` recorded problems (both
  the failed search and the old session folder), so future runs do not need to discover
  these problems again.

### Technical Conclusions

This result supports the idea from section 1: packaging the connection and login logic
into a reusable driver — here, as a Skill instead of an MCP server — removes the login
guessing problem and needs a less powerful model. Sonnet 5 succeeded right away on a task
that needed Opus in section 1, and that Haiku could not do at all.

A skill is different from a plain CLAUDE.md file or an MCP server, because it includes
not only tools but also *process knowledge*: the play loop, the stop rules, and the
memory structure. This combination is what stopped the "going off task" and "wandering
forever" problems we saw in section 1.

However, the failed search for The Statue's Room shows a real limit of this approach. The
skill only lets the agent "walk and look," not "search" or "go directly to a place." So
any goal that needs finding an unknown room is still limited by the step budget, and can
still fail even with good tooling. Fixing this would need a different kind of tool — for
example, an MCP tool connected to the MUD's own room database — not just a better prompt.

The memory setup worked better here than the plain markdown files in section 1, because
the skill enforces some structure through templates and a clear rule: never turn the map
into one fixed path. Still, it is only markdown, so the scaling problem from section 1 is
delayed, not solved. Managing old sessions is also still left to the agent's judgment. A
small fix to `mud_start.sh` — checking if the old process is really still running, not
just checking if the folder exists — would remove this last small issue.

Overall, this architecture works better than the plain agent-file approach in section 1.
It succeeded with a mid-level model on the first try, needed no trial and error with the
login, and can be reused for new goals in this MUD without redesigning the agent each
time.
