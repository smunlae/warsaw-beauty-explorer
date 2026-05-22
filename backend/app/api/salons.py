from __future__ import annotations

import json

from backend.app.core.database import get_db
from backend.app.models.salon import Salon
from backend.app.schemas.salon import SalonDetail, SalonListItem, SalonUpdate
from fastapi import APIRouter, Depends, HTTPException, Query
from scraper.pipeline import build_dedupe_key
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()


def _services_from_db(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


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
        price_range=salon.price_range,
        services_offered=_services_from_db(salon.services_offered),
    )


@router.get("", response_model=list[SalonListItem])
def list_salons(
    district: str | None = Query(default=None),
    service: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[SalonListItem]:
    stmt = select(Salon).order_by(Salon.reviews_count.desc(), Salon.name.asc())
    if district:
        stmt = stmt.where(Salon.district == district)
    if q:
        like_value = f"%{q}%"
        stmt = stmt.where(Salon.name.ilike(like_value) | Salon.address.ilike(like_value))
    if service:
        stmt = stmt.where(Salon.services_offered.ilike(f"%{service}%"))
    salons = db.execute(stmt).scalars().all()
    return [_salon_to_list_item(salon) for salon in salons]


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
        update_data["services_offered"] = json.dumps(update_data["services_offered"], ensure_ascii=False)

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
