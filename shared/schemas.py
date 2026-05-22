from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class SalonIngestion(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source_name: str = Field(min_length=1)
    source_url: str | None = None
    name: str = Field(min_length=1)
    address: str = Field(min_length=1)
    district: str = Field(min_length=1)
    rating: float | None = Field(default=None, ge=0, le=5)
    reviews_count: int = Field(default=0, ge=0)
    phone_number: str | None = None
    website_url: str | None = None
    social_media_url: str | None = None
    services_offered: list[str] = Field(default_factory=list)
    price_range: str | None = None

    @field_validator("source_url", "phone_number", "website_url", "social_media_url", "price_range", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class ScraperConfig(BaseModel):
    source: str = "booksy"
    pages: int = Field(default=2, ge=1, le=50)
    headless: bool = True
    base_url: str | None = None
    page_delay_ms: int = Field(default=1500, ge=0, le=10000)
