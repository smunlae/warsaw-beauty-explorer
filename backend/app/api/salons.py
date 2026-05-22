from __future__ import annotations

import json

from backend.app.core.database import get_db
from backend.app.models.salon import Salon
from backend.app.schemas.salon import SalonDetail, SalonListItem, SalonUpdate
from fastapi import APIRouter, Depends, HTTPException, Query
from scraper.pipeline import build_dedupe_key
from sqlalchemy import case, select
from sqlalchemy.orm import Session

router = APIRouter()


def _services_from_db(value: str | None) -> list[str] | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, list) else None


def _salon_to_detail(salon: Salon) -> SalonDetail:
    data = {column.name: getattr(salon, column.name) for column in Salon.__table__.columns}
    data["services_offered"] = _services_from_db(salon.services_offered)
    return SalonDetail.model_validate(data)


def _salon_to_list_item(salon: Salon) -> SalonListItem:
    return SalonListItem(
        id=salon.id,
        name=salon.name,
        district=salon.district,
        rating=salon.rating,
        reviews_count=salon.reviews_count,
        cover_image_url=salon.cover_image_url,
        price_range=salon.price_range,
        services_offered=_services_from_db(salon.services_offered),
    )


@router.get("", response_model=list[SalonListItem])
def list_salons(
    district: str | None = Query(default=None),
    service: str | None = Query(default=None),
    q: str | None = Query(default=None),
    sort_by: str = Query(default="reviews_count", pattern="^(reviews_count|rating|name|price)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> list[SalonListItem]:
    stmt = select(Salon)
    if district:
        stmt = stmt.where(Salon.district == district)
    if q:
        like_value = f"%{q}%"
        stmt = stmt.where(Salon.name.ilike(like_value) | Salon.address.ilike(like_value))
    if service:
        stmt = stmt.where(Salon.services_offered.ilike(f"%{service}%"))
    stmt = stmt.order_by(*_sort_order(sort_by, sort_order))
    salons = db.execute(stmt).scalars().all()
    return [_salon_to_list_item(salon) for salon in salons]


@router.get("/districts", response_model=list[str])
def list_districts(db: Session = Depends(get_db)) -> list[str]:
    rows = db.execute(
        select(Salon.district)
        .where(Salon.district.is_not(None))
        .distinct()
        .order_by(Salon.district.asc())
    ).scalars().all()
    return [district for district in rows if district]


@router.get("/{salon_id}", response_model=SalonDetail)
def get_salon(salon_id: int, db: Session = Depends(get_db)) -> SalonDetail:
    salon = db.get(Salon, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    return _salon_to_detail(salon)


@router.patch("/{salon_id}", response_model=SalonDetail)
def update_salon(salon_id: int, payload: SalonUpdate, db: Session = Depends(get_db)) -> SalonDetail:
    salon = db.get(Salon, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "services_offered" in update_data:
        services = update_data["services_offered"]
        update_data["services_offered"] = json.dumps(services, ensure_ascii=False) if services else None

    for field, value in update_data.items():
        setattr(salon, field, value)

    if {"source_name", "source_url", "name", "address"} & update_data.keys():
        salon.dedupe_key = build_dedupe_key(
            source_name=salon.source_name,
            source_url=salon.source_url,
            name=salon.name,
            address=salon.address,
        )

    db.add(salon)
    db.commit()
    db.refresh(salon)
    return _salon_to_detail(salon)


def _sort_order(sort_by: str, sort_order: str):
    descending = sort_order == "desc"
    if sort_by == "rating":
        ordered_rating = Salon.rating.desc() if descending else Salon.rating.asc()
        return (ordered_rating.nullslast(), Salon.name.asc())
    if sort_by == "name":
        return (Salon.name.desc() if descending else Salon.name.asc(),)
    if sort_by == "price":
        ordered_price = Salon.price_range.desc() if descending else Salon.price_range.asc()
        return (
            case((Salon.price_range.is_(None), 1), else_=0).asc(),
            ordered_price,
            Salon.name.asc(),
        )
    ordered_reviews = Salon.reviews_count.desc() if descending else Salon.reviews_count.asc()
    return (ordered_reviews, Salon.name.asc())
