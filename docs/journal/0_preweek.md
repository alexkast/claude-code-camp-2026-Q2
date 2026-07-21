# Preweek Technical Documentation
 
## Technical Goal
 
My technical goal for Preweek (Explore) is to determine which agent architecture is able
to drive a MUD as a real player, as groundwork for a future Player Journey Agent.
 
## Technical Uncertainty
 
- I'm uncertain if a weaker model (Haiku) can handle the MUD's login sequence without an
  explicit, purpose-built script.
- I'm uncertain if plain markdown files are enough for reliable world navigation and
  memory, or if they will become brittle as the world grows.
- I'm uncertain how much the architecture itself (a bare `CLAUDE.md` vs. a packaged
  Skill) affects reliability, even when the underlying goal and prompt stay the same.

## Technical Hypotheses
 
- I think that without a ready-made login script, the agent will get stuck at the entry
  point of the game, because the MUD's login flow is not something a general-purpose
  model can infer correctly on the first try.
- I think a Skill with a working driver already built in will be more reliable than a
  bare agent file, because it removes the connection and login problem from the model's
  responsibility.
- I think both of these approaches are only good as **temporary, testing setups**, not as
  a permanent solution. Both burn a lot of tokens for something that should be
  deterministic. A permanent solution needs: a durable and well-defined storage layer, a
  proven workflow, and a dedicated agent built specifically for this task — not a
  general-purpose coding harness repurposed as the solution.

## Technical Observations
 
### 1. An agent file with referenced files (`CLAUDE.md` + `data/*.md`)
 
I used one agent file with plain markdown memory (`player.md`, `world.md`,
`journal.md`), rewritten every loop, starting with the smallest model and escalating
only if it failed.
 
- **Haiku 4.5 — failed.** It never reached the goal: instead of driving the session step
  by step, it kept writing throwaway Python/telnet scripts, misread the login flow
  (creating unwanted extra characters), and went off task. Token usage was not
  unusually high, but it took a long time — repeatedly retrying instead of converging.
- **Opus 4.8 — succeeded.** It handled the login correctly on the first try, built one
  reusable background process instead of rewriting scripts, completed the goal, and
  updated memory correctly. It ran quickly, but at a noticeably higher token cost.
### 2. Agent Skills driven by main agent (`~/skills`, `play-mud`)
 
I packaged the same task as a Claude Code Skill with a working session driver, a login
reference doc, and memory templates, called directly from the main agent (no subagent).
 
- **Sonnet 5 — succeeded on the first try.** Login worked without issues, since the
  driver already encodes the login flow — the tooling solved it, not a smarter model.
  On a second run from a different starting room, it reused the saved world map instead
  of needing the route re-explained.
- A harder, open-ended goal was **not** completed: the agent explored within its step
  budget, never found the target room, and stopped and reported back as instructed
  rather than wandering indefinitely.
### 3. AI workflow automation platform (`n8n`)
 
- I attempted to evaluate `n8n`, but couldn't complete a fair test — it needs a fairly
  complex workflow plus a separate client to interact with it (I've used Telegram for
  that before).
- **Correction to my initial assumption:** Python access in n8n doesn't require a paid
  plan — it's free even self-hosted. The real limit is on **n8n Cloud**: Python code
  there can't import any libraries (it runs via Pyodide/WebAssembly, not a full
  runtime). Full Python is only available self-hosted — a real constraint for a
  socket-heavy use-case like this.

## Technical Conclusions
 
- Skills and Subagents are capable of driving the MUD; a bare agent file only succeeds
  with a strong, more expensive model, and even then only after solving the connection
  and login problem on its own.
- The architecture matters more than the model. With the *same* prompt and memory
  design, Haiku failed and Opus succeeded on a bare agent file — but with a Skill that
  already encodes the login flow, a mid-tier model (Sonnet 5) succeeded on the first try.
  This shows that packaging connection/login logic into a reusable driver removes model
  dependency as a risk.
- Plain markdown memory works for a single, short goal, but both architectures are only
  suitable as **temporary, exploratory setups** for a process that should be
  deterministic (logging in, sending a known command sequence). The cost shows up
  differently depending on the model: Haiku was not token-expensive but was slow,
  repeatedly retrying instead of converging; Opus converged quickly but at a real token
  cost. Either way, the underlying login and navigation logic should not need an LLM to
  work it out every time.
- A permanent solution requires three things I do not have yet: a durable and
  well-defined storage layer (not ad-hoc markdown), a proven and repeatable workflow, and
  a dedicated agent built specifically for this task — not a general-purpose coding
  harness stretched to fit it.
- `n8n` could not be evaluated fairly in this round. It needs a non-trivial workflow to
  be built plus a separate client to interact with it (e.g. Telegram), and on the Cloud
  tier, Python code execution is restricted to no library imports at all — a real
  constraint for a use-case built around managing a live socket session.

## Key Takeaway
 
Both the bare agent-file approach and the Skill-based approach can drive the MUD, but
only as temporary, exploratory setups — not as an architecture I would run permanently.
Depending on the model, that cost shows up either as slow, repeated retries (Haiku) or
as real token expense (Opus) — for what is fundamentally a deterministic process. Either
way, both still depend on a coding harness doing work it was not built for. A permanent solution
needs a durable storage layer, a proven workflow, support logging and monitoring options, and a purpose-built agent — not a
general-purpose harness repurposed to play the role of one.
