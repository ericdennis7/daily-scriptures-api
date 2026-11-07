# Daily Scriptures API

A small API that returns Bible verses in several translations, plus a verse of the day that changes at each user's local midnight.

Base URL: `https://api.thesimplebeliever.com`

## Endpoints

### `GET /`

Returns a welcome message.

```json
{"message": "Welcome to the Daily Scriptures API. ..."}
```

### `GET /random`

Returns a random verse from our verse pool (not the entire Bible).

| Parameter | Required | Description |
| --- | --- | --- |
| `version` | No | Translation code, e.g. `esv`. Omit to get every translation. |

Without `version`:

```json
{
  "reference": "Psalms 56:8",
  "versions": {"asv": "...", "esv": "...", "kjv": "..."}
}
```

With `version=esv`:

```json
{
  "reference": "Psalms 56:8",
  "version": "esv",
  "text": "..."
}
```

### `GET /verse-of-the-day`

Returns the same verse for the whole day in the user's timezone. The verse changes at local midnight.

| Parameter | Required | Description |
| --- | --- | --- |
| `version` | No | Translation code, e.g. `esv`. Omit to get every translation. |
| `tz` | No | IANA timezone name, e.g. `America/New_York`. Overrides the detected timezone. |

Timezone priority:

1. `tz` query parameter, if given.
2. The visitor's timezone, detected by Cloudflare, when deployed.
3. UTC.

Without `version`:

```json
{
  "date": "2026-11-06",
  "reference": "Psalms 56:8",
  "versions": {"asv": "...", "esv": "...", "kjv": "..."}
}
```

With `version=esv`:

```json
{
  "date": "2026-11-06",
  "reference": "Psalms 56:8",
  "version": "esv",
  "text": "..."
}
```

`date` is the date in the timezone used for the lookup.

## Examples

```bash
curl "https://api.thesimplebeliever.com/random"
curl "https://api.thesimplebeliever.com/random?version=esv"
curl "https://api.thesimplebeliever.com/verse-of-the-day?version=asv&tz=America/New_York"
```

## Translations

Codes are lowercase: `asv`, `csb`, `esv`, `kjv`, `nasb`, `niv`, `nkjv`, `web`. Some translations may not have every verse. A request for a missing translation returns `404`.

## Errors

| Status | Cause |
| --- | --- |
| `400` | Unknown timezone in `tz`. |
| `404` | Unknown translation, or the translation has no text for the verse of the day. |

Error bodies look like `{"detail": "..."}`.

## Caching

`/verse-of-the-day` sends `Cache-Control: public, max-age=N`, where `N` is the number of seconds until the next local midnight. Clients and CDNs can cache the response until then.

Use the `tz` parameter when caching through a shared cache. Otherwise, a cached response for one timezone may be served to visitors in another.

## Development

Install dependencies and start the local Worker:

```bash
uv sync
uv run pywrangler dev
```

The API runs at `http://localhost:8787`.

## Data

- `data-gathering/verses.json`: references scraped from topverses.com.
- `data-gathering/verses_10plus.json`: verses from `10plus.csv` with text for each translation.
- `data-gathering/bible-versions/`: source XML for each translation.
- `src/verses_data.py`: generated from the JSON by `data-gathering/build_verses_module.py`.
