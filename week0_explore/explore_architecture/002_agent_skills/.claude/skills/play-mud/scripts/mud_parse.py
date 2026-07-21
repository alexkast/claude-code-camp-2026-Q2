#!/usr/bin/env python3
"""
Best-effort parser for a chunk of tbaMUD output (ANSI already stripped, as
produced by mud_send.sh) into structured fields.

Usage:
    mud_send.sh .mud-session "look" | python3 mud_parse.py

Prints JSON:
    {
      "room_name": "The Bakery",
      "exits": ["s"],
      "vitals": {"hp": 21, "mana": 100, "moves": 80}
    }

This is a heuristic, not a full MUD client -- combat spam, NPC speech, dark
rooms, and shop listings will not parse into these fields. Always look at
the raw text too; treat this as a shortcut for the common "room + exits +
vitals" case, not a replacement for reading the output.
"""
import json
import re
import sys


def parse(text: str) -> dict:
    exits = []
    m = re.search(r"\[\s*Exits:\s*([^\]]*)\]", text)
    if m:
        exits = m.group(1).split()

    room_name = ""
    for line in text.split("\n"):
        s = line.strip()
        if s and not s.startswith("[") and not s.startswith(">>>") and 3 < len(s) < 70:
            room_name = s
            break

    vitals = {}
    vm = re.search(r"(\d+)H\s+(\d+)M\s+(\d+)V", text)
    if vm:
        vitals = {"hp": int(vm.group(1)), "mana": int(vm.group(2)), "moves": int(vm.group(3))}

    return {"room_name": room_name, "exits": exits, "vitals": vitals}


if __name__ == "__main__":
    print(json.dumps(parse(sys.stdin.read()), indent=2))
