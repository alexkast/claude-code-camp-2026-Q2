# World Map (graph)

Each room lists its exits and where each one leads (`unknown` if
unexplored). Never delete a known room, and never write the map as a fixed
A -> B step list -- if it can only answer "how do I get to X" from one
specific starting room, the map is wrong. It should work as a graph you can
navigate from anywhere you've already been.

No room literally named "The Statue's Room" was found during a ~50-command
sweep of central Midgaard (see journal). Closest matches: Market Square
(has a large statue -- the "Midgaard Worm" statue) and By The Temple Altar
(has a 10ft sitting statue of Odin). Neither room is *named* "The Statue's
Room".

## The Bakery
- Small bakery; sweet smell of danish and bread; shelves of bread/Danish;
  a small sign on the counter (readable, explains `buy`/`list`); a baker
  NPC present. This is also the character's login/spawn room.
- Exits:
  - s -> The Armory (assumed; character was later found standing in Armory)

## The Armory
- Wide assortment of armor on walls/windows; helmets, shields, suits of
  armor for sale; a small note on the wall; an armorer NPC.
- Exits:
  - n -> Main Street (Armory/Bakery junction)

## Main Street (Armory/Bakery junction)
- "South ... Armory, ... bakery is to the north ... East ... market square."
- Exits:
  - n -> The Bakery
  - s -> The Armory
  - e -> Market Square
  - w -> Main Street (Mages Guild/city gate junction)

## Main Street (Mages Guild / city gate junction)
- "South ... Guild of Magic Users ... east towards the market square.
  The magic shop is to the north ... west is the city gate."
- Exits:
  - n -> The Magic Shop
  - s -> The Entrance To The Mages' Guild
  - e -> Main Street (Armory/Bakery junction)
  - w -> Inside The West Gate Of Midgaard

## The Entrance To The Mages' Guild
- Small, poorly lit hall; an ATM; a cityguard; a sorcerer guarding entrance.
- Exits:
  - n -> Main Street (Mages Guild/city gate junction)
  - s -> unknown (not explored, guarded)

## The Magic Shop
- Counter with racks of (presumably) magic items; a wizard NPC.
- Exits:
  - s -> Main Street (Mages Guild/city gate junction)

## Inside The West Gate Of Midgaard
- Two small towers connected by a footbridge over the city gate; a
  cityguard.
- Exits:
  - e -> Main Street (Mages Guild/city gate junction)
  - s -> Wall Road (south stretch, unexplored)
  - w -> unknown (outside city, unexplored)

## Market Square
- "Famous Square of Midgaard." A large, peculiar statue in the middle --
  `look statue` reveals it depicts "the Midgaard Worm, stretching around
  the Palace of Midgaard." NOT named "The Statue's Room" despite the statue.
- Exits:
  - n -> The Temple Square
  - s -> The Common Square
  - e -> Main Street (General Store/Pet Shop junction)
  - w -> Main Street (Armory/Bakery junction)

## The Temple Square
- Marble steps up to the temple gate; Clerics' Guild entrance to the west;
  the old Grunting Boar Inn to the east; a marble fountain.
- Exits:
  - n -> The Temple Of Midgaard
  - s -> Market Square
  - w -> The Entrance To The Clerics' Guild
  - e -> The Entrance Hall Of The Grunting Boar Inn

## The Temple Of Midgaard
- Southern end of the temple hall; giant marble blocks; ancient wall
  paintings; an ATM.
- Exits:
  - n -> By The Temple Altar
  - s / d -> The Temple Square
  - w -> Reading Room (unexplored)
  - e -> Donation Room (unexplored)

## By The Temple Altar
- Northern end of temple; huge white marble altar; a ten-foot tall SITTING
  STATUE OF ODIN towers behind the altar. Room name is "By The Temple
  Altar", not "The Statue's Room".
- Exits:
  - n -> Behind The Temple Altar
  - s -> The Temple Of Midgaard

## Behind The Temple Altar
- Dirt path north of the altar, leads toward the Dragonhelm Mountains.
- Exits:
  - n -> unknown (countryside, unexplored further)
  - s -> By The Temple Altar

## The Entrance To The Clerics' Guild
- Small modest hall; an ATM; a knight templar guarding the entrance to
  the bar (north exit blocked to low-level characters -- "guard
  humiliates you").
- Exits:
  - e -> The Temple Square
  - n -> blocked/unknown (bar, guarded)

## The Entrance Hall Of The Grunting Boar Inn
- Simple functional furniture; Post Office smell drifts in from the
  north; staircase up to reception; bar to the east.
- Exits:
  - w -> The Temple Square
  - n -> Post Office (unexplored)
  - e -> bar (unexplored)
  - u -> reception (unexplored)

## Main Street (General Store/Pet Shop junction)
- "North is the general store ... main street continues east ... west
  you see and hear the market place, south a small door leads into the
  Pet Shop."
- Exits:
  - n -> The General Store
  - s -> The Pet Shop
  - w -> Market Square
  - e -> Main Street (Weapon Shop/Swordsmen Guild junction)

## The General Store
- Items stacked on shelves behind the counter; a small note on the wall;
  a janitor; a grocer.
- Exits:
  - s -> Main Street (General Store/Pet Shop junction)

## The Pet Shop
- Small crowded store, cages and animals; a sign on the wall; a Pet Shop
  Boy NPC.
- Exits:
  - n -> Main Street (General Store/Pet Shop junction)

## Main Street (Weapon Shop/Swordsmen Guild junction)
- "North is the weapon shop and ... south is the Guild of Swordsmen.
  East you leave town and ... west the street leads to the market square."
- Exits:
  - n -> Weapon Shop (unexplored)
  - s -> The Entrance Hall To The Guild Of Swordsmen
  - w -> Main Street (General Store/Pet Shop junction)
  - e -> unknown (leaves town, unexplored)

## The Entrance Hall To The Guild Of Swordsmen
- Careful-what-you-say hall; an ATM; a knight guarding entrance.
- Exits:
  - n -> Main Street (Weapon Shop/Swordsmen Guild junction)
  - e -> The Bar Of Swordsmen

## The Bar Of Swordsmen
- Furniture in pieces; a bulletin board; a waiter.
- Exits:
  - w -> The Entrance Hall To The Guild Of Swordsmen
  - s -> The Tournament And Practice Yard

## The Tournament And Practice Yard
- Practice yard of the fighters; a well leading down; guildmaster NPC
  sharpening an axe here.
- Exits:
  - n -> The Bar Of Swordsmen
  - d -> unknown (well, unexplored)

## The Common Square
- People passing, talking; poor alley to the west, dark alley to the
  east; nasty smell from the south.
- Exits:
  - n -> Market Square
  - s -> The Dump
  - w -> The Eastern End Of Poor Alley
  - e -> Dark Alley (unexplored)

## The Dump
- Garbage dump; large junction of pipes -- sewer system entrance.
- Exits:
  - n -> The Common Square
  - d -> unknown (sewer, unexplored)

## The Eastern End Of Poor Alley
- Poor alley; Grubby Inn to the south (unexplored); alley continues west;
  a cityguard, an "odif yltsaeb", a beastly fido present.
- Exits:
  - e -> The Common Square
  - s -> Grubby Inn (unexplored)
  - w -> Poor Alley

## Poor Alley
- Alley continues east; city wall to the west; a beggar NPC.
- Exits:
  - e -> The Eastern End Of Poor Alley
  - w -> Wall Road (north stretch)

## Wall Road (north stretch, by poor alley)
- Next to the western city wall; road continues north and south; letters
  written on the wall.
- Exits:
  - e -> Poor Alley
  - n -> unknown (unexplored)
  - s -> unknown (unexplored, may connect toward Inside The West Gate)

## Unexplored branches still open
Reading Room and Donation Room (off Temple Of Midgaard), the guarded bar
north of Clerics' Guild entrance, Post Office / Inn bar / Inn upstairs
(off Grunting Boar Inn entrance hall), Weapon Shop, the road east out of
town (Weapon Shop junction), Dark Alley (east of Common Square), Grubby
Inn (south of Eastern End of Poor Alley), the well down from the
Tournament Yard, the sewer down from The Dump, and the far ends of Wall
Road and the countryside path north of the temple.
