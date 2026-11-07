import importlib.resources
import random
from contextvars import ContextVar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, HTTPException, Query, Response

from verses_data import VERSES

app = FastAPI(title="Daily Scriptures API")

# Set per request by the Worker entrypoint from Cloudflare's detected timezone.
# ContextVars are isolated per request task, so concurrent requests don't collide.
CLIENT_TIMEZONE: ContextVar[str | None] = ContextVar("client_timezone", default=None)

ENTRIES = list(VERSES.values())


def available_versions() -> list[str]:
    versions: set[str] = set()
    for entry in ENTRIES:
        versions.update(entry["versions"].keys())
    return sorted(versions)

@app.get("/")
def root():
    return {"message": "Welcome to the Daily Scriptures API. Please visit https://github.com/ericdennis7/daily-scriptures-api for documentation."}

@app.get("/random")
def random_verse(
    version: str | None = Query(
        default=None,
        description="Bible version code, e.g. esv. Omit to return all versions.",
    ),
):
    if version is None:
        entry = random.choice(ENTRIES)
        return {"reference": entry["reference"], "versions": entry["versions"]}

    key = version.lower()
    if key not in available_versions():
        raise HTTPException(
            status_code=404,
            detail=f"Unknown version '{version}'. Available: {', '.join(available_versions())}",
        )

    candidates = [e for e in ENTRIES if key in e["versions"]]
    entry = random.choice(candidates)
    return {
        "reference": entry["reference"],
        "version": key,
        "text": entry["versions"][key],
    }


# Fixed shuffle order: every verse appears once per cycle before any repeat.
# The seed keeps the order identical across requests and Worker instances.
CYCLE_SEED = 20261106
DAILY_ORDER = ENTRIES[:]
random.Random(CYCLE_SEED).shuffle(DAILY_ORDER)


def resolve_timezone(tz_name: str | None) -> ZoneInfo:
    """Use the given IANA name, else UTC. Raises 400 for unknown names."""
    if not tz_name:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        pass
    # Pyodide/Workers has no system tz database; read the zone file from the tzdata package
    try:
        with importlib.resources.files("tzdata.zoneinfo").joinpath(tz_name).open("rb") as f:
            return ZoneInfo.from_file(f, key=tz_name)
    except (FileNotFoundError, IsADirectoryError, ModuleNotFoundError, ValueError, OSError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown timezone '{tz_name}'. Lookup error: {type(exc).__name__}: {exc}",
        )


def seconds_until_next_local_midnight(now: datetime) -> int:
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((tomorrow - now).total_seconds())


@app.get("/verse-of-the-day")
async def verse_of_the_day(
    response: Response,
    version: str | None = Query(
        default=None,
        description="Bible version code, e.g. esv. Omit to return all versions.",
    ),
    tz: str | None = Query(
        default=None,
        description="IANA timezone, e.g. America/New_York. Overrides the detected timezone.",
    ),
):
    # Priority: explicit ?tz= > Cloudflare-detected timezone > UTC
    zone = resolve_timezone(tz or CLIENT_TIMEZONE.get())
    now = datetime.now(zone)
    # Days since the epoch, mod cycle length: walks through every verse before repeating
    index = now.toordinal() % len(DAILY_ORDER)
    entry = DAILY_ORDER[index]

    # Same verse all day in the user's timezone, so caches expire at their local midnight
    response.headers["Cache-Control"] = (
        f"public, max-age={seconds_until_next_local_midnight(now)}"
    )

    if version is None:
        return {
            "date": now.date().isoformat(),
            "reference": entry["reference"],
            "versions": entry["versions"],
        }

    key = version.lower()
    if key not in available_versions():
        raise HTTPException(
            status_code=404,
            detail=f"Unknown version '{version}'. Available: {', '.join(available_versions())}",
        )
    if key not in entry["versions"]:
        raise HTTPException(
            status_code=404,
            detail=f"Version '{key}' is not available for today's verse.",
        )
    return {
        "date": now.date().isoformat(),
        "reference": entry["reference"],
        "version": key,
        "text": entry["versions"][key],
    }
