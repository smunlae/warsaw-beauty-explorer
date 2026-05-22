from __future__ import annotations

import math
import threading

from backend.app.core.config import settings
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from scraper.detail_pipeline import enrich_salon_details
from scraper.pipeline import run_pipeline
from shared.schemas import ScraperConfig

router = APIRouter()

SALONS_PER_PAGE = 20
BOOKSY_CATEGORY_OPTIONS = {"hair", "nails", "both"}
_status_lock = threading.Lock()
_scraper_status: dict[str, object] = {
    "status": "idle",
    "source": "booksy",
    "category": "hair",
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
_detail_status: dict[str, object] = {
    "status": "idle",
    "total": 0,
    "processed": 0,
    "remaining": 0,
    "progress_percent": 0,
    "enriched": 0,
    "failed": 0,
    "error": None,
}


def _set_status(**updates: object) -> None:
    with _status_lock:
        _scraper_status.update(updates)


def _get_status() -> dict[str, object]:
    with _status_lock:
        return dict(_scraper_status)


def _set_detail_status(**updates: object) -> None:
    with _status_lock:
        _detail_status.update(updates)


def _get_detail_status() -> dict[str, object]:
    with _status_lock:
        return dict(_detail_status)


def _booksy_categories(category: str) -> list[str]:
    if category == "both":
        return ["hair", "nails"]
    return [category]


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


def _run_detail_enrichment(limit: int | None) -> None:
    def update_progress(processed: int, total: int) -> None:
        progress_base = max(total, 1)
        _set_detail_status(
            status="running",
            total=total,
            processed=processed,
            remaining=max(total - processed, 0),
            progress_percent=round((processed / progress_base) * 100),
        )

    try:
        result = enrich_salon_details(limit=limit, progress_callback=update_progress)
    except Exception as exc:
        _set_detail_status(status="failed", error=str(exc))
        raise

    _set_detail_status(
        status="finished",
        total=result.total,
        processed=result.total,
        remaining=0,
        progress_percent=100,
        enriched=result.enriched,
        failed=result.failed,
        error=None,
    )


@router.post("/run")
def run_scraper(
    background_tasks: BackgroundTasks,
    source: str = Query(default="booksy"),
    category: str = Query(default="hair", pattern="^(hair|nails|both)$"),
    salon_count: int = Query(default=settings.booksy_default_pages * SALONS_PER_PAGE, ge=1, le=1000),
) -> dict[str, object]:
    current_status = _get_status()
    if current_status["status"] == "running":
        raise HTTPException(status_code=409, detail="Scraper is already running")

    categories = _booksy_categories(category)
    pages = math.ceil(salon_count / SALONS_PER_PAGE)
    pages_total = pages * len(categories)
    requested_total = salon_count * len(categories)
    config = ScraperConfig(
        source=source,
        pages=pages,
        headless=settings.booksy_headless,
        base_url=None,
        booksy_categories=categories,
    )
    _set_status(
        status="running",
        source=source,
        category=category,
        requested_salon_count=requested_total,
        pages_total=pages_total,
        pages_completed=0,
        parsed_count=0,
        remaining_count=requested_total,
        progress_percent=0,
        inserted=0,
        updated=0,
        error=None,
    )
    background_tasks.add_task(_run_scraper, config, requested_total)
    return _get_status()


@router.get("/status")
def get_scraper_status() -> dict[str, object]:
    return _get_status()


@router.post("/details/run")
def run_detail_enrichment(
    background_tasks: BackgroundTasks,
    limit: int | None = Query(default=None, ge=1, le=1000),
) -> dict[str, object]:
    current_status = _get_detail_status()
    if current_status["status"] == "running":
        raise HTTPException(status_code=409, detail="Detail enrichment is already running")

    _set_detail_status(
        status="running",
        total=limit or 0,
        processed=0,
        remaining=limit or 0,
        progress_percent=0,
        enriched=0,
        failed=0,
        error=None,
    )
    background_tasks.add_task(_run_detail_enrichment, limit)
    return _get_detail_status()


@router.get("/details/status")
def get_detail_enrichment_status() -> dict[str, object]:
    return _get_detail_status()
