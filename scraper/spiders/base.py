from __future__ import annotations

from abc import ABC, abstractmethod

from shared.schemas import SalonIngestion, ScraperConfig


class BaseSpider(ABC):
    source_name: str

    @abstractmethod
    def scrape(self, config: ScraperConfig) -> list[SalonIngestion]:
        """Collect and normalize records for a source."""
