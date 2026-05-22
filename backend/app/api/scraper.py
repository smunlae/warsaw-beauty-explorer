from __future__ import annotations

import math
import threading

from backend.app.core.config import settings
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from scraper.pipeline import run_pipeline
from shared.schemas import ScraperConfig

router = APIRouter()

SALONS_PER_PAGE = 20
_status_lock = threading.Lock()
_scraper_status: dict[str, object] = {
    "status": "idle",
    "source": "booksy",
    "requested_salon_count": 0,
    "pages_total": 0,
    "pages_completed": 0,
    "parsed_count": 0,
    "remaining_count": 0,
    "progress_percent": 0,
    "inserted": 0,
    "updated": 0,
    "error": None,
}


def _set_status(**updates: object) -> None:
    with _status_lock:
        _scraper_status.update(updates)


def _get_status() -> dict[str, object]:
    with _status_lock:
        return dict(_scraper_status)


def _run_scraper(config: ScraperConfig, requested_salon_count: int) -> None:
    def update_progress(pages_completed: int, pages_total: int, parsed_count: int) -> None:
        progress_base = max(requested_salon_count, 1)
        progress_percent = min(100, round((parsed_count / progress_base) * 100))
        _set_status(
            status="running",
            pages_completed=pages_completed,
            pages_total=pages_total,
            parsed_count=parsed_count,
            remaining_count=max(requested_salon_count - parsed_count, 0),
            progress_percent=progress_percent,
        )

    try:
        result = run_pipeline(config, progress_callback=update_progress)
    except Exception as exc:
        _set_status(status="failed", error=str(exc))
        raise

    _set_status(
        status="finished",
        parsed_count=result.collected,
        remaining_count=max(requested_salon_count - result.collected, 0),
        progress_percent=100,
        inserted=result.inserted,
        updated=result.updated,
        error=None,
    )


@router.post("/run")
def run_scraper(
    background_tasks: BackgroundTasks,
    source: str = Query(default="booksy"),
    salon_count: int = Query(default=settings.booksy_default_pages * SALONS_PER_PAGE, ge=1, le=1000),
) -> dict[str, object]:
    current_status = _get_status()
    if current_status["status"] == "running":
        raise HTTPException(status_code=409, detail="Scraper is already running")

    pages = math.ceil(salon_count / SALONS_PER_PAGE)
    config = ScraperConfig(
        source=source,
        pages=pages,
        headless=settings.booksy_headless,
        base_url=settings.booksy_base_url if source == "booksy" else None,
    )
    _set_status(
        status="running",
        source=source,
        requested_salon_count=salon_count,
        pages_total=pages,
        pages_completed=0,
        parsed_count=0,
        remaining_count=salon_count,
        progress_percent=0,
        inserted=0,
        updated=0,
        error=None,
    )
    background_tasks.add_task(_run_scraper, config, salon_count)
    return _get_status()


@router.get("/status")
def get_scraper_status() -> dict[str, object]:
    return _get_status()
