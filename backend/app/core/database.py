from __future__ import annotations

from collections.abc import Generator

from backend.app.core.config import settings
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from backend.app.models import salon  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "salons" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("salons")}
    if "cover_image_url" in existing_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE salons ADD COLUMN cover_image_url VARCHAR(1000)"))
