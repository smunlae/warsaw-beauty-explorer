from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from shared.schemas import SalonIngestion, ScraperConfig

ProgressCallback = Callable[[int, int, int], None]


class BaseSpider(ABC):
    source_name: str

    @abstractmethod
    def scrape(self, config: ScraperConfig, progress_callback: ProgressCallback | None = None) -> list[SalonIngestion]:
        """Collect and normalize records for a source."""
