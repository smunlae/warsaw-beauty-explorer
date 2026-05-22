from __future__ import annotations

from playwright.sync_api import Playwright, sync_playwright
from scraper.parsers.booksy_parser import parse_booksy_listing_page
from scraper.spiders.base import BaseSpider, ProgressCallback
from scraper.spiders.registry import SpiderRegistry
from shared.schemas import SalonIngestion, ScraperConfig

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


@SpiderRegistry.register
class BooksySpider(BaseSpider):
    source_name = "booksy"

    def scrape(self, config: ScraperConfig, progress_callback: ProgressCallback | None = None) -> list[SalonIngestion]:
        with sync_playwright() as playwright:
            return self._scrape_with_playwright(playwright, config, progress_callback)

    def _scrape_with_playwright(
        self,
        playwright: Playwright,
        config: ScraperConfig,
        progress_callback: ProgressCallback | None,
    ) -> list[SalonIngestion]:
        browser = playwright.chromium.launch(headless=config.headless)
        context = browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()
        base_url = config.base_url or "https://booksy.com/pl-pl/s/fryzjer/3_warszawa"
        salons: list[SalonIngestion] = []

        try:
            for current_page in range(1, config.pages + 1):
                target_url = f"{base_url}/?businessesPage={current_page}"
                page.goto(target_url, wait_until="domcontentloaded")
                page.wait_for_timeout(config.page_delay_ms)
                page_salons = parse_booksy_listing_page(page.content())
                salons.extend(page_salons)
                if progress_callback:
                    progress_callback(current_page, config.pages, len(salons))
        finally:
            context.close()
            browser.close()

        return salons
