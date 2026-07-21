# Journal

## Run 1 — 2026-07-16
- **Goal:** Find the bakery and list what is on the menu.
- **Achieved:** Yes.
- **Steps used:** 5 in-game commands (d, s, w, n, list) — well under the 50 budget.
- **Route:** Temple Of Midgaard --d--> Temple Square --s--> Market Square --w--> Main Street --n--> The Bakery.
- **Menu:** A danish pastry (7), A bread (14), A waybread (73) — all unlimited stock.
- **Friction points:**
  - `confused` (login): The CLAUDE.md login is genuinely prompt-driven and easy to get wrong. `dummy` is an EXISTING character — after the name the server jumps straight to `Password:`. I initially assumed a name-confirmation ("Did I get that right? Y/N") step, which is actually the NEW-character path; sending "y" there created junk characters and derailed several attempts. Lesson: read the exact prompt, don't assume the sequence.
  - `blocked` (mechanics): Driving a long-lived async TCP session is the real difficulty, not the game. One-shot scripts that log in + explore + quit are fragile because timing and the branching login are hard to hardcode. What worked: a persistent background driver holding the socket, fed one command at a time via a FIFO, with all server output appended to a log I read between steps. This matches the intended observe/orient/decide/act loop far better than a monolithic script.
  - `overpowered` (navigation): Once logged in, the game itself hands you the map — every room description names where exits lead ("the bakery is to the north"), so finding the bakery took 4 moves with zero combat. The challenge is entirely in the harness/session plumbing, not the world.
