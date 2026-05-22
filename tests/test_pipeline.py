from __future__ import annotations

import json

from backend.app.core.database import Base
from backend.app.models.salon import Salon
from scraper.pipeline import build_dedupe_key, upsert_salons
from shared.schemas import SalonIngestion
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def _record(
    *,
    name: str = "Salon Test",
    source_url: str | None = "https://booksy.com/salon-test",
    rating: float | None = 4.5,
    reviews_count: int = 10,
    services_offered: list[str] | None = None,
) -> SalonIngestion:
    return SalonIngestion(
        source_name="booksy",
        source_url=source_url,
        name=name,
        address="ulica Testowa 1",
        district="Ochota",
        rating=rating,
        reviews_count=reviews_count,
        cover_image_url="https://cdn.example.com/cover.jpg",
        services_offered=services_offered,
        price_range="100-200 PLN",
    )


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_build_dedupe_key_prefers_source_url() -> None:
    key = build_dedupe_key(
        source_name="Booksy",
        source_url=" HTTPS://BOOKSY.COM/Profile ",
        name="Ignored",
        address="Ignored",
    )

    assert key == "source:booksy:https://booksy.com/profile"


def test_build_dedupe_key_falls_back_to_normalized_name_and_address() -> None:
    key = build_dedupe_key(
        source_name="Booksy",
        source_url=None,
        name="Salon Piękna!",
        address="ul. Testowa 1/2",
    )

    assert key == "fallback:booksy:salon-pi-kna:ul-testowa-1-2"


def test_upsert_salons_is_idempotent_and_updates_existing_row() -> None:
    db = _session()
    first = _record(rating=4.5, reviews_count=10, services_offered=["Cut"])
    second = _record(rating=4.9, reviews_count=25, services_offered=["Cut", "Color"])

    try:
        first_result = upsert_salons(db, [first])
        db.commit()
        second_result = upsert_salons(db, [second])
        db.commit()

        salons = db.execute(select(Salon)).scalars().all()
        assert first_result.inserted == 1
        assert first_result.updated == 0
        assert second_result.inserted == 0
        assert second_result.updated == 1
        assert len(salons) == 1
        assert salons[0].rating == 4.9
        assert salons[0].reviews_count == 25
        assert json.loads(salons[0].services_offered) == ["Cut", "Color"]
    finally:
        db.close()


def test_upsert_salons_skips_duplicate_records_within_one_batch() -> None:
    db = _session()
    record = _record()

    try:
        result = upsert_salons(db, [record, record])
        db.commit()

        count = len(db.execute(select(Salon)).scalars().all())
        assert result.inserted == 1
        assert result.updated == 0
        assert count == 1
    finally:
        db.close()
