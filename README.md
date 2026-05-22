# Warsaw Beauty Salon Explorer

Full-stack project for collecting Warsaw beauty salon data from Booksy  (using Playwright) and exposing it through a FastAPI API with a React UI.

## Stack

- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite
- Scraper: Playwright for page collection, Selectolax for parsing
- Frontend: React + Vite

## Project shape

- `backend/` - FastAPI app and database models
- `scraper/` - source spiders, parsers, and ETL pipeline
- `shared/` - Pydantic ingestion contracts shared by backend and scraper
- `frontend/` - React UI

Each data source is implemented as a spider class that inherits from `BaseSpider`. Booksy is the first spider. New sources can be added by creating another spider and registering it in `scraper/spiders/registry.py`.

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Frontend:

```bash
cd frontend
npm install
```

## Run scraper manually

```bash
python -m scraper.runner --source booksy --pages 2
```

The pipeline is idempotent: it updates existing salons by `source_name + source_url`, with a fallback to normalized `name + address`.

## Run backend

```bash
uvicorn backend.main:app --reload
```

API docs: http://localhost:8000/docs

## Run frontend

```bash
cd frontend
npm run dev
```

UI: http://localhost:5173

## Current fields

Collected now:

- name
- address
- district
- Booksy URL / source URL
- rating
- review count

Prepared for future enrichment:

- phone number
- website URL
- social media URL
- services offered
- price range

## Improvements with more time

- Add service-detail scraping from individual salon pages.
- Add Google Places/Yelp enrichment through official APIs.
- Add scraper run history and status polling instead of a "fire and forget" background task.
- Add tests for parser fixtures and API endpoints.
