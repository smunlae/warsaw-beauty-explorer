from __future__ import annotations

from scraper.spiders.base import BaseSpider


class SpiderRegistry:
    _spiders: dict[str, type[BaseSpider]] = {}

    @classmethod
    def register(cls, spider_cls: type[BaseSpider]) -> type[BaseSpider]:
        cls._spiders[spider_cls.source_name] = spider_cls
        return spider_cls

    @classmethod
    def create(cls, source_name: str) -> BaseSpider:
        try:
            spider_cls = cls._spiders[source_name]
        except KeyError as exc:
            available = ", ".join(sorted(cls._spiders)) or "none"
            raise ValueError(f"Unknown scraper source '{source_name}'. Available sources: {available}") from exc
        return spider_cls()

    @classmethod
    def available_sources(cls) -> list[str]:
        return sorted(cls._spiders)
