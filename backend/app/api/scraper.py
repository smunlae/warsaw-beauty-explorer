from __future__ import annotations

from backend.app.core.config import settings
from fastapi import APIRouter, BackgroundTasks, Query
from scraper.pipeline import run_pipeline
from shared.schemas import ScraperConfig

router = APIRouter()


def _run_scraper(config: ScraperConfig) -> None:
    run_pipeline(config)


@router.post("/run")
def run_scraper(
    background_tasks: BackgroundTasks,
    source: str = Query(default="booksy"),
    pages: int = Query(default=settings.booksy_default_pages, ge=1, le=50),
) -> dict[str, str]:
    config = ScraperConfig(
        source=source,
        pages=pages,
        headless=settings.booksy_headless,
        base_url=settings.booksy_base_url if source == "booksy" else None,
    )
    background_tasks.add_task(_run_scraper, config)
    return {"status": "scraping_started", "source": source}
