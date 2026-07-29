# Sources Architecture Guide

This folder contains the internal abstraction for all listing providers.

## Goal

Every provider (RSS or HTML scraper) must expose the same interface through `BaseSource`.
The rest of the bot should not care where items come from.

## Current Sources

- `RSSSource`: wraps existing RSS parsing behavior.
- `RedditSource`: maps Reddit URLs to official RSS (`/.rss`) and delegates parsing to RSS source.
- `TablonSource`: HTML scraper for tablondeanuncios.com listings.

## Base Contract

Every source class must inherit from `BaseSource` and implement:

- `validate() -> dict[str, Any]`
- `parse_items(limit: int = 10) -> Optional[list[Item]]`

`Item` is the normalized model consumed by the rest of the system.

## Built-in Robustness from BaseSource

Use `BaseSource` HTTP helper in HTML sources:

- `_request_text(url: Optional[str] = None)`

It provides:

- HTTP timeout
- retries
- structured logs with source context
- scraping metrics counters

Available metrics (`get_metrics()`):

- `http_requests`
- `http_retries`
- `http_failures`
- `parse_runs`
- `items_extracted`
- `html_structure_fallbacks`

## HTML Structure Drift Detection

When implementing a scraper, define:

- primary selectors (expected current markup)
- fallback selectors (backward compatibility)

If fallback selectors are used while primary selectors fail, log a warning and increment `html_structure_fallbacks`.
This is the signal that a portal changed markup and selectors should be reviewed.

## How to Add a New Source

1. Create a file in `app/sources/`, for example `idealista_source.py`.
2. Implement a class inheriting from `BaseSource`.
3. Reuse `_request_text()` for HTTP fetches.
4. Parse provider-specific HTML into `Item` objects.
5. Implement `validate()` with clear errors and entry count.
6. Register provider detection and source selection in `SourceFactory.from_url()`.
7. Keep `resolve_registration_url()` logic consistent for that provider if URL normalization is needed.
8. Add unit tests under `tests/unit/` for:
   - provider detection in factory
   - valid extraction
   - invalid/empty page
   - drift fallback path
   - retry/failure behavior (if custom)

## Rules

- Do not change orchestrator/scheduler business flow when adding a source.
- Do not change Telegram or database contracts.
- Keep output mapped to `Item` so downstream processing remains unchanged.
