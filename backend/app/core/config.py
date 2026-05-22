from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = PROJECT_ROOT / "backend" / "salons.db"


class Settings(BaseModel):
    app_name: str = "Warsaw Beauty Salon Explorer"
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    booksy_base_url: str = os.getenv("BOOKSY_BASE_URL", "https://booksy.com/pl-pl/s/fryzjer/3_warszawa")
    booksy_default_pages: int = int(os.getenv("BOOKSY_DEFAULT_PAGES", "2"))
    booksy_headless: bool = os.getenv("BOOKSY_HEADLESS", "true").lower() in {"1", "true", "yes"}


settings = Settings()
