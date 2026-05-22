from __future__ import annotations

from datetime import datetime

from backend.app.core.database import Base
from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column


class Salon(Base):
    __tablename__ = "salons"
    __table_args__ = (
        UniqueConstraint("source_name", "source_url", name="uq_salons_source_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviews_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    social_media_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    services_offered: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_range: Mapped[str | None] = mapped_column(String(120), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(700), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
