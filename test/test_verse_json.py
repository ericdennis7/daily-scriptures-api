"""
Check the verse JSON files in data-gathering/ for missing or bad data.

For each JSON file that has a "verses" key, every entry should have:
  - a "reference" string
  - a "versions" dict that contains every version in bible-versions/

Run from anywhere:
    python3 test/test_verse_json.py

Exits with status 1 if any problems are found.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data-gathering"
VERSIONS_DIR = DATA_DIR / "bible-versions"

REFERENCE = re.compile(r"^(?:[1-3] )?[A-Za-z][A-Za-z.]*(?: [A-Za-z.]+)* \d+[:.]\d+(?:\s*[-–]\s*\d+)?$")


def expected_versions() -> set[str]:
    """'en_kjv.xml' -> 'kjv'."""
    return {p.stem.split("_", 1)[1] for p in VERSIONS_DIR.glob("*.xml")}


def check_file(path: Path, expected: set[str]) -> list[str]:
    problems: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    verses = data.get("verses")
    if not isinstance(verses, dict):
        return ["no 'verses' object"]
    if verses and all(isinstance(entry, str) for entry in verses.values()):
        return None  # plain-string format, versions not added yet: not checked

    seen_refs: dict[str, str] = {}
    for rank, entry in verses.items():
        label = f"#{rank}"

        if isinstance(entry, str):
            problems.append(f"{label}: plain string, versions not added yet")
            continue
        if not isinstance(entry, dict):
            problems.append(f"{label}: entry is {type(entry).__name__}, expected object")
            continue

        reference = entry.get("reference")
        if not reference:
            problems.append(f"{label}: missing 'reference'")
            label_ref = label
        else:
            label_ref = f"{label} {reference}"
            if not REFERENCE.match(reference):
                problems.append(f"{label_ref}: reference does not look like a verse")
            if reference in seen_refs:
                problems.append(f"{label_ref}: duplicate of #{seen_refs[reference]}")
            else:
                seen_refs[reference] = rank

        versions = entry.get("versions")
        if not isinstance(versions, dict):
            problems.append(f"{label_ref}: missing 'versions'")
            continue

        missing = sorted(expected - set(versions))
        if missing:
            problems.append(f"{label_ref}: missing versions {', '.join(missing)}")

        for key, text in versions.items():
            if not isinstance(text, str) or not text.strip():
                problems.append(f"{label_ref}: empty text for '{key}'")

    return problems


def main() -> int:
    expected = expected_versions()
    if not expected:
        print(f"No XML versions found in {VERSIONS_DIR}")
        return 1
    print(f"Expected versions: {', '.join(sorted(expected))}")

    total_problems = 0
    checked = 0
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            problems = check_file(path, expected)
        except json.JSONDecodeError as exc:
            problems = [f"invalid JSON: {exc}"]
        if problems is None:
            print(f"\n{path.name}: skipped (plain strings, versions not added yet)")
            continue
        if problems and problems[0] == "no 'verses' object":
            continue  # not a verse file

        checked += 1
        total_problems += len(problems)
        status = "OK" if not problems else f"{len(problems)} problem(s)"
        print(f"\n{path.name}: {status}")
        for problem in problems[:50]:
            print(f"  - {problem}")
        if len(problems) > 50:
            print(f"  ... and {len(problems) - 50} more")

    print(f"\nChecked {checked} file(s), {total_problems} problem(s) total.")
    return 1 if total_problems else 0


if __name__ == "__main__":
    sys.exit(main())
