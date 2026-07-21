# Journal

Append one entry per run below. Tag friction points with `confused` /
`blocked` / `bored` / `overpowered` -- including anything that made the
session hard to drive mechanically, not just in-game outcomes.

## Run 1 -- 2026-07-21
- **Goal:** Find the bakery and list the menu.
- **Achieved:** yes
- **Steps used:** 3 (`look`, `read sign`, `list`)
- **Friction points:** none. Character happened to spawn directly inside
  The Bakery, so no navigation was needed -- got lucky on the starting
  room. Worth noting for future runs: don't assume the bakery is always
  the spawn point, since this wasn't verified across multiple logins.

## Run 2 -- 2026-07-21
- **Goal:** Go to "The Statue's Room" and describe what's inside.
- **Achieved:** no
- **Steps used:** ~50 (hit the budget cap)
- **Friction points:** `blocked` / `confused`. Login this time did NOT
  spawn in The Bakery -- character was found standing in The Armory,
  confirming position persists between sessions rather than always
  resetting to a fixed spawn (contradicts the "got lucky on spawn" note
  from Run 1 -- update: position is carried over, not randomized/fixed).
  Swept the whole reachable central-Midgaard street grid plus the temple,
  swordsmen guild, clerics guild entrance, common square/alleys, and the
  dump, and never found a room literally named "The Statue's Room".
  Two candidate statues exist in differently-named rooms (Market Square's
  "Midgaard Worm" statue, and the sitting Odin statue in "By The Temple
  Altar") -- neither room carries the target name, so didn't treat either
  as a match. Also found a stale `.mud-session/` from an earlier,
  already-dead process (pid in the file no longer running) that had to be
  removed before a fresh session would start cleanly -- worth checking
  process liveness, not just directory existence, before reusing a
  session dir. Left several branches unexplored (temple's Reading/
  Donation Room, Grunting Boar Inn's post office/bar/upstairs, Weapon
  Shop, Dark Alley, Grubby Inn, the well, the sewer, far Wall Road, and
  the countryside path) -- stopped at the step budget rather than
  guessing further or wandering deeper without new information.

## Run 3 -- 2026-07-21
- **Goal:** Go to the bakery and list the menu (re-run, character was in
  The Pet Shop this time).
- **Achieved:** yes
- **Steps used:** 5 (`n`, `w`, `w`, `n`, `list`) using the known route
  Pet Shop -> Main Street (general store/pet shop junction) -> Market
  Square -> Main Street (armory/bakery junction) -> The Bakery.
- **Friction points:** none. The `world.md` graph from prior runs made
  this trivial to path-find regardless of current position, confirming
  the graph (not a fixed step list) approach pays off.
