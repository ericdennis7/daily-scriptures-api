"""Renumber verse entries: every key >= START becomes key - 1.

Example: 777 -> 776, 778 -> 777, ...

Usage (from data-gathering/):
    python3 renumber_verses.py                  # uses verses_10plus.json
    python3 renumber_verses.py verses.json
"""

import json
import sys
from pathlib import Path

START = 777
DEFAULT_FILE = Path(__file__).parent / "verses_10plus.json"


def renumber(verses: dict[str, dict], start: int = START) -> dict[str, dict]:
    keys = {int(k) for k in verses}
    # Abort before writing if a renumbered key would collide with an existing one.
    targets = {k - 1 for k in keys if k >= start}
    collisions = sorted(targets & (keys - {k for k in keys if k >= start}))
    if collisions:
        raise SystemExit(f"Collision: keys {collisions} already exist; nothing written.")

    renumbered: dict[str, dict] = {}
    for key, value in verses.items():
        n = int(key)
        new_key = n - 1 if n >= start else n
        renumbered[str(new_key)] = value
    return dict(sorted(renumbered.items(), key=lambda item: int(item[0])))


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    data = json.loads(path.read_text(encoding="utf-8"))
    data["verses"] = renumber(data["verses"])
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Renumbered keys >= {START} in {path.name}")


if __name__ == "__main__":
    main()
