from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SalonListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    district: str
    rating: float | None = None
    reviews_count: int
    cover_image_url: str | None = None
    price_range: str | None = None
    services_offered: list[str] | None = None


class SalonDetail(SalonListItem):
    address: str
    source_name: str
    source_url: str | None = None
    phone_number: str | None = None
    website_url: str | None = None
    social_media_url: str | None = None
    created_at: datetime
    updated_at: datetime


class SalonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    address: str | None = Field(default=None, min_length=1)
    district: str | None = Field(default=None, min_length=1)
    cover_image_url: str | None = None
    phone_number: str | None = None
    website_url: str | None = None
    social_media_url: str | None = None
    services_offered: list[str] | None = None
    price_range: str | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    reviews_count: int | None = Field(default=None, ge=0)
