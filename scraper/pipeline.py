from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable

from backend.app.core.database import SessionLocal, init_db
from backend.app.models.salon import Salon
from scraper.spiders.booksy import BooksySpider  # noqa: F401 - registers BooksySpider
from scraper.spiders.registry import SpiderRegistry
from shared.schemas import SalonIngestion, ScraperConfig
from sqlalchemy import select
from sqlalchemy.orm import Session

_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")
ProgressCallback = Callable[[int, int, int], None]


@dataclass(frozen=True)
class PipelineResult:
    source: str
    collected: int
    inserted: int
    updated: int


def run_pipeline(config: ScraperConfig, progress_callback: ProgressCallback | None = None) -> PipelineResult:
    init_db()
    spider = SpiderRegistry.create(config.source)
    records = spider.scrape(config, progress_callback=progress_callback)

    db = SessionLocal()
    try:
        result = upsert_salons(db, records)
        db.commit()
        return PipelineResult(
            source=config.source,
            collected=len(records),
            inserted=result.inserted,
            updated=result.updated,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def upsert_salons(db: Session, records: list[SalonIngestion], batch_size: int = 20) -> PipelineResult:
    inserted = 0
    updated = 0
    seen_keys: set[str] = set()

    for record in records:
        dedupe_key = build_dedupe_key(
            source_name=record.source_name,
            source_url=record.source_url,
            name=record.name,
            address=record.address,
        )
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        existing = db.execute(select(Salon).where(Salon.dedupe_key == dedupe_key)).scalar_one_or_none()
        if existing:
            _apply_record(existing, record, dedupe_key)
            updated += 1
        else:
            db.add(_new_salon(record, dedupe_key))
            inserted += 1

        if (inserted + updated) % batch_size == 0:
            db.commit()

    return PipelineResult(source="mixed", collected=len(records), inserted=inserted, updated=updated)


def build_dedupe_key(source_name: str, source_url: str | None, name: str, address: str) -> str:
    if source_url:
        return f"source:{_normalize(source_name)}:{source_url.strip().lower()}"
    return f"fallback:{_normalize(source_name)}:{_normalize(name)}:{_normalize(address)}"


def _new_salon(record: SalonIngestion, dedupe_key: str) -> Salon:
    salon = Salon(dedupe_key=dedupe_key)
    _apply_record(salon, record, dedupe_key)
    return salon


def _apply_record(salon: Salon, record: SalonIngestion, dedupe_key: str) -> None:
    salon.source_name = record.source_name
    salon.source_url = record.source_url
    salon.name = record.name
    salon.address = record.address
    salon.district = record.district
    salon.rating = record.rating
    salon.reviews_count = record.reviews_count
    salon.cover_image_url = record.cover_image_url
    salon.phone_number = record.phone_number
    salon.website_url = record.website_url
    salon.social_media_url = record.social_media_url
    salon.services_offered = json.dumps(record.services_offered, ensure_ascii=False) if record.services_offered else None
    salon.price_range = record.price_range
    salon.dedupe_key = dedupe_key


def _normalize(value: str) -> str:
    normalized = _NORMALIZE_RE.sub("-", value.lower()).strip("-")
    return normalized or "unknown"
