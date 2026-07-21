# World Map (graph)

Format: each room lists its exits and where each leads (`unknown` if unexplored).

## The Temple Of Midgaard
- Southern end of the temple hall. An ATM is in the wall. Recall point.
- Exits:
  - n -> unknown
  - e -> the donation room (alcove)
  - s -> unknown
  - w -> the Reading Room
  - d -> The Temple Square
- Notes: hub of the city is the temple square, reached via `d`.

## The Temple Square
- Fountain, cityguard, a gelatinous blob (mob). Marble steps lead up to temple.
- Exits:
  - n -> unknown
  - e -> the Grunting Boar Inn
  - s -> the market square (center of Midgaard)
  - w -> the Clerics' Guild
  - u -> The Temple Of Midgaard
- Notes: market square (s) is the center; bakery likely off the market / Baker St.

## Market Square
- The famous Square of Midgaard. Peculiar statue in the middle. Cityguard.
- Exits:
  - n -> The Temple Square
  - e -> Main Street (east)
  - s -> the common square (unexplored)
  - w -> Main Street (west) -> leads toward the bakery

## Main Street (west of Market Square)
- Passing through the City of Midgaard.
- Exits:
  - n -> The Bakery
  - e -> Market Square
  - s -> the Armory (entrance)
  - w -> unknown (main street continues)

## The Bakery
- Small bakery, sweet scent of danish and fine bread. A sign is on the counter.
- Mob: the baker (calm, non-hostile).
- Exits:
  - s -> Main Street (west)
- Menu (`list`):
  - A danish pastry — 7 coins (Unlimited)
  - A bread — 14 coins (Unlimited)
  - A waybread — 73 coins (Unlimited)

### Route to the bakery (from Temple recall)
Temple Of Midgaard --d--> Temple Square --s--> Market Square --w--> Main Street --n--> The Bakery
