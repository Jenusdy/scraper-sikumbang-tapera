# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Web scraper that collects subsidized housing data from TAPERA's SIKUMBANG API (sikumbang.tapera.go.id) and stores it in MySQL.

## Running the Scraper

```bash
# From project root, ensure config.ini exists with valid database credentials
python main.py
```

The scraper:
1. Fetches paginated location list from search API
2. For each location, fetches detail JSON (housing complex + units)
3. Inserts into MySQL using `INSERT IGNORE` (duplicates skipped)
4. Logs progress to `sikumbang_scraper.log`

## Database Setup

```bash
mysql -h <host> -u <user> -p < database.sql
```

Requires `config.ini` in project root with `[database]` section (host, user, password, database). This file is gitignored.

## Architecture

- **main.py**: Entry point. `scrape_sikumbang_all_data()` orchestrates the two-level scraping:
  - Level 1: `GET /ajax/lokasi/search?page=N&limit=100` → paginated location list
  - Level 2: `GET /lokasi-perumahan/{id}/json` → detailed housing complex + unit data
- **Helper functions**: `parse_date()`, `parse_year()`, `calculate_aggregation()`, `build_values()` transform API responses into insert-ready tuples
- **Logging**: Structured format `%(asctime)s | %(levelname)s | %(message)s` to sikumbang_scraper.log

## Key Patterns

- `INSERT IGNORE` handles duplicates via `cursor.rowcount == 1` check
- `time.sleep(0.5)` between detail requests (rate limiting)
- Per-location error handling (one failure doesn't stop the scrape)
- Aggregation counts (subsidi/komersil units sold) calculated from unit list