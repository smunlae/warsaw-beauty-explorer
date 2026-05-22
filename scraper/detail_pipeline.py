from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from backend.app.core.database import SessionLocal, init_db
from backend.app.models.salon import Salon
from scraper.spiders.booksy import BooksySpider
from sqlalchemy import select

DetailProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class DetailPipelineResult:
    total: int
    enriched: int
    failed: int


def enrich_salon_details(limit: int | None = None, progress_callback: DetailProgressCallback | None = None) -> DetailPipelineResult:
    init_db()
    db = SessionLocal()
    spider = BooksySpider()
    enriched = 0
    failed = 0

    try:
        stmt = (
            select(Salon)
            .where(Salon.source_name == "booksy")
            .where(Salon.source_url.is_not(None))
            .order_by(Salon.services_offered.is_not(None).asc(), Salon.name.asc())
        )
        if limit:
            stmt = stmt.limit(limit)
        salons = db.execute(stmt).scalars().all()
        total = len(salons)

        urls = [str(salon.source_url) for salon in salons if salon.source_url]
        details_by_url = spider.scrape_details(
            urls,
            progress_callback=(lambda processed, total, _parsed: progress_callback(processed, total))
            if progress_callback
            else None,
        )

        for index, salon in enumerate(salons, start=1):
            detail = details_by_url.get(str(salon.source_url))
            if detail is None:
                failed += 1
                if progress_callback:
                    progress_callback(index, total)
                continue

            if detail.services_offered is not None:
                salon.services_offered = json.dumps(detail.services_offered, ensure_ascii=False)
            if detail.price_range is not None:
                salon.price_range = detail.price_range
            db.add(salon)
            db.commit()
            enriched += 1

            if progress_callback:
                progress_callback(index, total)

        return DetailPipelineResult(total=total, enriched=enriched, failed=failed)
    finally:
        db.close()
