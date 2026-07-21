# tbaMUD Text Interface Reference

This documents exactly what the server sends and expects, so you don't have
to rediscover it by trial and error. It was captured from a real session
against the MUD at `localhost:4000`.

## Connecting

Plain TCP to `localhost:4000`. Right after connecting, the server sends a
client-detection preamble that you can ignore:

```
Attempting to Detect Client, Please Wait...
Collecting Protocol Information... Please Wait.
[...]
                               T  B  A  M  U  D
                                   2 0 2 5
By what name do you wish to be known?
```

## Logging in an EXISTING character (the common case)

`mud_driver.py` automates this path.

1. Send the character name. If the name exists, the server goes **straight**
   to `Password:` -- there is no "Did I get that right? (Y/N)" step here.
   That confirmation only happens for a brand-new name (see below). Assuming
   it always appears is the single most common mistake when driving this
   login by hand.
2. Send the password. It is not echoed back.
3. The server sends a welcome banner, possibly a line like
   `1 LOGIN FAILURE SINCE LAST SUCCESSFUL LOGIN.`, then:
   ```
   *** PRESS RETURN:
   ```
   Send a blank line (just `\r\n`).
4. The main menu appears:
   ```
   Welcome to tbaMUD!
   0) Exit from tbaMUD.
   1) Enter the game.
   2) Enter description.
   3) Read the background story.
   4) Change password.
   5) Delete this character.

      Make your choice:
   ```
   Send `1` to enter the game.
5. You land in the game, with a short welcome line followed immediately by
   the starting room description (see "Room format" below).

## Creating / logging in a NEW character

**Not automated by `mud_driver.py`** -- if `mud_start.sh` reports
`===LOGIN-NEEDS-ATTENTION===`, drive the rest by hand with `mud_send.sh`,
using this sequence:

1. Send the name. Since it doesn't exist yet, the server asks:
   `Did I get that right, <Name> (Y/N)?` -- send `y`.
2. `New character. Give me a password for <Name>:` -- send a password.
3. `Please retype password:` -- send it again.
4. `What is your sex (M/F)?` -- send `M` or `F`.
5. Class selection:
   ```
   Select a class:
     [C]leric
     [T]hief
     [W]arrior
     [M]agic-user

   Class:
   ```
   Send one letter, e.g. `w`.
6. From here it rejoins the existing-character flow: welcome banner,
   `*** PRESS RETURN:`, blank line, main menu, `1` to enter the game.

## Room format

A typical room, once you're in the game:

```
The Bakery
   You are standing inside the small bakery.  A sweet scent of danish and
fine bread fills the room.  The bread and Danish are arranged in fine order
on the shelves, and seem to be of the finest quality.
A small sign is on the counter.
[ Exits: s ]
The baker looks at you calmly, wiping flour from his face with one hand.

21H 100M 80V (news) (motd) >
```

- First line: room name.
- Then a free-text description (may wrap across several lines).
- `[ Exits: <letters> ]` -- ground truth for topology. Directions seen:
  `n s e w u d` (north/south/east/west/up/down), sometimes `ne nw se sw`.
- Any remaining lines before the prompt: notable objects/mobs in the room.
- The prompt line, e.g. `21H 100M 80V (news) (motd) >` -- the three numbers
  are **HP, Mana, Movement points**, in that order. A bare prompt like this
  with no new text after it means the server is idle and waiting for your
  next command.

`mud_parse.py` extracts room name / exits / vitals from a chunk like this.

## It's an asynchronous session

Combat rounds, other players' actions, and room events (a mob wandering in,
weather messages, etc.) can arrive **without you sending anything**. This is
why the driver reads until the server goes quiet for a bit, rather than
reading a fixed number of bytes or lines after each command. If you see
output arrive that you didn't ask for, that's normal -- read it, update your
notes, and continue.

## Output encoding

Raw server output contains ANSI color escape codes and `\r\n` line endings.
`mud_send.sh` already strips both (`\x1b\[[0-9;]*[a-zA-Z]` for ANSI, `\r` for
carriage returns) so its output is plain, readable text. If you ever read
`session.log` directly instead of going through `mud_send.sh`, strip these
yourself first.

## Useful commands observed in this world

`look`, `n`/`s`/`e`/`w`/`u`/`d` (movement), `list` (shop menu when standing
in a shop), `buy <item>`, `score` (character stats), `inventory` / `i`,
`equipment` / `eq`, `flee` (retreat from combat). This list is not
exhaustive -- when in doubt, try the obvious verb and read what comes back.
