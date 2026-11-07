"""
Add the scripture text for each Bible version to verses.json.

Reads every XML file in bible-versions/ (e.g. en_kjv.xml -> "kjv"), looks up
each verse reference in verses.json, and writes the text back as:

{
  "verses": {
    "1": {
      "reference": "John 3:16",
      "versions": {
        "kjv": "For God so loved the world...",
        "niv": "For God so loved the world..."
      }
    },
    ...
  }
}
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).parent
VERSES_FILE = BASE_DIR / "verses_10plus.json"
VERSIONS_DIR = BASE_DIR / "bible-versions"

REFERENCE = re.compile(r"^(.+?)\s+(\d+)[:.](\d+)(?:\s*[-–]\s*(\d+))?$")

# Names used in the CSV that differ from the book names in the XML files.
# Keys are normalized (lowercase, letters and digits only).
BOOK_ALIASES = {
    "psalm": "psalms",
    "ps": "psalms",
    "prov": "proverbs",
    "phil": "philippians",
    "eph": "ephesians",
    "isa": "isaiah",
    "gal": "galatians",
    "jer": "jeremiah",
    "josh": "joshua",
    "heb": "hebrews",
    "rev": "revelation",
    "deut": "deuteronomy",
    "gen": "genesis",
    "1cor": "1corinthians",
    "2cor": "2corinthians",
    "ipeter": "1peter",
    "songofsongs": "songofsolomon",
}


def normalize_book(name: str) -> str:
    """Lowercase and strip everything but letters and digits, e.g. '1 John' -> '1john'."""
    key = re.sub(r"[^a-z0-9]", "", name.lower())
    return BOOK_ALIASES.get(key, key)


def version_key(path: Path) -> str:
    """'en_kjv.xml' -> 'kjv'."""
    stem = path.stem
    return stem.split("_", 1)[1] if "_" in stem else stem


def load_version(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Return {normalized_book: {chapter: {verse: text}}}."""
    index: dict[str, dict[str, dict[str, str]]] = {}
    root = ET.parse(path).getroot()
    for book in root.iter("b"):
        book_key = normalize_book(book.get("n", ""))
        chapters = index.setdefault(book_key, {})
        for chapter in book.iter("c"):
            verses = chapters.setdefault(chapter.get("n", ""), {})
            for verse in chapter.iter("v"):
                text = "".join(verse.itertext()).strip()
                verses[verse.get("n", "")] = text
    return index


def lookup(index, reference: str) -> str | None:
    match = REFERENCE.match(reference.strip())
    if not match:
        return None
    book, chapter, start, end = match.groups()
    # Drop leading zeros: "Genesis 3:03" -> chapter "3", verse "3"
    chapter = str(int(chapter))
    start = str(int(start))
    chapter_verses = index.get(normalize_book(book), {}).get(chapter, {})

    if end is None:
        return chapter_verses.get(start)

    # Verse range within one chapter, e.g. "Matthew 6:14-15" -> both verses joined
    first, last = int(start), int(end)
    if last < first:
        return None
    parts = []
    for number in range(first, last + 1):
        text = chapter_verses.get(str(number))
        if text is None:
            return None
        parts.append(text)
    return " ".join(parts)


def main() -> None:
    data = json.loads(VERSES_FILE.read_text(encoding="utf-8"))
    verses = data["verses"]

    version_files = sorted(VERSIONS_DIR.glob("*.xml"))
    indexes = {version_key(p): load_version(p) for p in version_files}
    print(f"Loaded versions: {', '.join(indexes)}")

    missing: list[str] = []
    new_verses: dict[str, dict] = {}

    for rank, entry in verses.items():
        # Support both the old plain-string format and the new dict format
        reference = entry if isinstance(entry, str) else entry["reference"]
        texts = {}
        for key, index in indexes.items():
            text = lookup(index, reference)
            if text is None:
                missing.append(f"{reference} ({key})")
            else:
                texts[key] = text
        new_verses[rank] = {"reference": reference, "versions": texts}

    data["verses"] = new_verses
    VERSES_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Updated {len(new_verses)} verses in {VERSES_FILE}")
    if missing:
        print(f"{len(missing)} lookups had no match:")
        for item in missing:
            print(f"  - {item}")


if __name__ == "__main__":
    main()
