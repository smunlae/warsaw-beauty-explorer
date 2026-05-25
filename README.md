# Warsaw Beauty Salon Explorer

Full-stack MVP for collecting, enriching, storing, and browsing Warsaw beauty salon data from Booksy.

The project focuses on a reproducible programmatic data pipeline: Playwright collects listing/detail pages, Selectolax parses structured data, SQLAlchemy stores normalized records in SQLite, FastAPI exposes the data, and React provides a simple explorer UI.

## Stack

- Backend: FastAPI, Pydantic v2, SQLAlchemy, SQLite
- Scraper: Playwright, Selectolax
- Frontend: React + Vite
- Tests: pytest

## Features

- Booksy listing scraping for:
  - hair salons: `https://booksy.com/pl-pl/s/fryzjer/3_warszawa`
  - nail salons: `https://booksy.com/pl-pl/s/paznokcie/3_warszawa`
  - both categories in one run
- Detail enrichment from individual salon pages:
  - services offered
  - price range
- Idempotent SQLite upsert flow:
  - primary dedupe: `source_name + source_url`
  - fallback dedupe: normalized `name + address`
- Background scraper runs through FastAPI.
- Scraper progress status for listing and detail parsing.
- SQLite WAL mode and busy timeout to reduce locking during active scraping.
- React UI with:
  - salon cards with cover images
  - 5-star rating display with partial star fill
  - district/search/service filters
  - sorting by review count, rating, name, and price
  - editable salon details panel
  - refresh controls for hair, nails, or both

## Project Structure

```text
warsaw-beauty-explorer/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # config, database setup
│   │   ├── models/       # SQLAlchemy models
│   │   └── schemas/      # API Pydantic schemas
│   ├── main.py
│   └── salons.db
├── scraper/
│   ├── parsers/          # Selectolax / payload parsers
│   ├── spiders/          # BaseSpider, registry, BooksySpider
│   ├── detail_pipeline.py
│   ├── pipeline.py
│   └── runner.py
├── shared/               # shared ingestion schemas
├── frontend/             # React/Vite app
└── tests/                # pytest unit tests
```

Each external source is modeled as a spider class implementing `BaseSpider`. Booksy is the first concrete spider and is registered through `SpiderRegistry`. New sources can be added by creating another spider class and registering it without rewriting the pipeline core.

## Data Fields

Currently collected from listing pages:

- business name
- address
- district
- Booksy URL
- rating
- number of reviews
- cover image URL

Currently enriched from detail pages:

- services offered
- price range

Prepared nullable fields:

- phone number
- website URL
- social media URL

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Frontend:

```powershell
cd frontend
npm install
```

## Run The Scraper Manually

Hair salons:

```powershell
python -m scraper.runner --source booksy --category hair --pages 2 --headless
```

Nail salons:

```powershell
python -m scraper.runner --source booksy --category nails --pages 2 --headless
```

Both categories:

```powershell
python -m scraper.runner --source booksy --category both --pages 2 --headless
```

`--pages 2` means two pages per selected category. For `both`, this runs two hair pages and two nails pages.

## Run Backend

```powershell
uvicorn backend.main:app --reload
```

API docs:

```text
http://localhost:8000/docs
```

Main endpoints:

- `GET /api/v1/salons`
- `GET /api/v1/salons/{id}`
- `PATCH /api/v1/salons/{id}`
- `GET /api/v1/salons/districts`
- `POST /api/v1/scraper/run?source=booksy&category=hair&salon_count=100`
- `GET /api/v1/scraper/status`
- `POST /api/v1/scraper/details/run?limit=100`
- `GET /api/v1/scraper/details/status`

Supported listing categories:

- `hair`
- `nails`
- `both`

## Run Frontend

```powershell
cd frontend
npm run dev
```

UI:

```text
http://localhost:5173
```

The refresh panel lets the user choose:

- Hair
- Nails
- Both

The `Salons per category` field is converted to pages internally using 20 salons per Booksy listing page. For example, `100` salons means 5 pages for one category, or 10 total pages when `Both` is selected.

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Current test coverage focuses on logic that should remain stable and easy to verify:

- Booksy listing parser
- Booksy detail parser
- spider category URL selection
- dedupe key generation
- idempotent SQLite upsert
- selected API helper functions

## Notes

- The listing parser supports regular Booksy HTML and saved browser `view-source:` HTML wrappers.
- Detail parsing uses Booksy page state to extract service categories, services, and prices.
- The scraper writes to SQLite in batches to reduce database lock time.
- The UI intentionally stays simple; the main technical emphasis is the data collection and enrichment pipeline.

## Future Improvements

- Add Google Places validation through the official API.
- Persist scraper run history in the database.
- Add integration tests for FastAPI endpoints.
- Add source/category labels in the UI cards if multiple sources are introduced.
- Add pagination or virtualized rendering for larger datasets.
