"""
Generate src/verses_data.py from data-gathering/verses.json.

Python Workers bundle Python modules, so the verse data is written out as a
Python dict that the API can import. Re-run this after updating verses.json.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
VERSES_FILE = BASE_DIR / "verses.json"
OUTPUT_FILE = BASE_DIR.parent / "src" / "verses_data.py"


def main() -> None:
    verses = json.loads(VERSES_FILE.read_text(encoding="utf-8"))["verses"]
    # JSON text is a valid Python dict literal here (no true/false/null values)
    literal = json.dumps(verses, indent=2, ensure_ascii=False)
    OUTPUT_FILE.write_text(
        '"""Generated from data-gathering/verses.json. Do not edit by hand."""\n\n'
        f"VERSES = {literal}\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(verses)} verses to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
