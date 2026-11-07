"""
Fetch top-ranked Bible verse references from topverses.com.

Pages 1-50, roughly 10 verses per page. Only the verse reference
(e.g. "Galatians 3:13") is kept. Output is written to verses.json:

{
  "verses": {
    "1": "John 3:16",
    "2": "John 1:1",
    ...
  }
}
"""

import json
import re
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://www.topverses.com/Bible/&pg={page}&a=ajax"
FIRST_PAGE = 51
LAST_PAGE = 100
DELAY_SECONDS = 5.0
OUTPUT_FILE = Path(__file__).parent / "verses.json"

# Matches the verse heading in each block, e.g.:
# <h2><a href="/Bible/Galatians/3/13">\n Galatians 3:13\n </a></h2>
VERSE_HEADING = re.compile(
    r'<h2>\s*<a href="/Bible/[^"]*">\s*([^<]+?)\s*</a>\s*</h2>',
    re.IGNORECASE,
)
REFERENCE = re.compile(r"^(?:[1-3]\s)?[A-Za-z][A-Za-z .]*\s\d+:\d+$")


def fetch_page(page: int) -> str:
    url = BASE_URL.format(page=page)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_references(html: str) -> list[str]:
    references = []
    for match in VERSE_HEADING.finditer(html):
        reference = match.group(1).strip()
        if REFERENCE.match(reference):
            references.append(reference)
    return references


def main() -> None:
    verses: dict[str, str] = {}
    seen: set[str] = set()

    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        try:
            html = fetch_page(page)
        except Exception as exc:
            print(f"page {page}: failed ({exc})")
            continue

        new_refs = [ref for ref in parse_references(html) if ref not in seen]
        for ref in new_refs:
            seen.add(ref)
            verses[str(len(verses) + 1)] = ref

        print(f"page {page}: {len(new_refs)} new verses (total {len(verses)})")
        time.sleep(DELAY_SECONDS)

    OUTPUT_FILE.write_text(
        json.dumps({"verses": verses}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved {len(verses)} verses to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
