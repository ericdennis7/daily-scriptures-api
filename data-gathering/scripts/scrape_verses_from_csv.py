"""
Extract verse references from the Text column of 10plus.csv.

Rows are deduplicated by the OSIS column, so alternate names for the same
verse (e.g. "Phil 4:13" and "Philippians 4:13") are kept once, using the
first (most popular) spelling. Output is written to verses_10plus.json in
the same format as verses.json:

{
  "verses": {
    "1": "Philippians 4:13",
    "2": "John 14:6",
    ...
  }
}

verses.json is not modified.
"""

import csv
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "10plus.csv"
OUTPUT_FILE = BASE_DIR / "verses_10plus.json"
MAX_VERSES = 2500

# Book name (capitalized), chapter, and verse or verse range, e.g. "Psalm 118.24", "1 John 3:16-17"
VALID_REFERENCE = re.compile(
    r"^(?:[1-3] )?[A-Z][A-Za-z.]*(?: [A-Za-z.]+)* \d+[:.]\d+(?:\s*[-–]\s*\d+)?$"
)


def main() -> None:
    verses: dict[str, str] = {}
    seen: set[str] = set()
    seen_refs: set[str] = set()
    skipped = 0

    with CSV_FILE.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if len(verses) >= MAX_VERSES:
                break

            reference = (row.get("Text") or "").strip()
            osis = (row.get("OSIS") or "").strip()

            if not VALID_REFERENCE.match(reference):
                skipped += 1
                continue

            key = osis or reference.lower()
            ref_key = " ".join(reference.lower().split())
            if key in seen or ref_key in seen_refs:
                continue
            seen.add(key)
            seen_refs.add(ref_key)
            verses[str(len(verses) + 1)] = reference

    OUTPUT_FILE.write_text(
        json.dumps({"verses": verses}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(verses)} unique verses to {OUTPUT_FILE}")
    print(f"Skipped {skipped} rows with no Text value")


if __name__ == "__main__":
    main()
