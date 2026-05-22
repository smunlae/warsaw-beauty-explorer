from __future__ import annotations

from playwright.sync_api import Page, Playwright, sync_playwright
from scraper.parsers.booksy_detail_parser import SalonDetailEnrichment, parse_booksy_detail_payload
from scraper.parsers.booksy_parser import parse_booksy_listing_page
from scraper.spiders.base import BaseSpider, ProgressCallback
from scraper.spiders.registry import SpiderRegistry
from shared.schemas import SalonIngestion, ScraperConfig

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

BOOKSY_CATEGORY_URLS = {
    "hair": "https://booksy.com/pl-pl/s/fryzjer/3_warszawa",
    "nails": "https://booksy.com/pl-pl/s/paznokcie/3_warszawa",
}


@SpiderRegistry.register
class BooksySpider(BaseSpider):
    source_name = "booksy"

    def scrape(self, config: ScraperConfig, progress_callback: ProgressCallback | None = None) -> list[SalonIngestion]:
        with sync_playwright() as playwright:
            return self._scrape_with_playwright(playwright, config, progress_callback)

    def scrape_detail(self, url: str, headless: bool = True, page_delay_ms: int = 1500) -> SalonDetailEnrichment:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1280, "height": 720},
            )
            page = context.new_page()
            try:
                return self._scrape_detail_page(page, url, page_delay_ms)
            finally:
                context.close()
                browser.close()

    def scrape_details(
        self,
        urls: list[str],
        headless: bool = True,
        page_delay_ms: int = 1500,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, SalonDetailEnrichment | None]:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1280, "height": 720},
            )
            page = context.new_page()
            results: dict[str, SalonDetailEnrichment | None] = {}
            try:
                for index, url in enumerate(urls, start=1):
                    try:
                        results[url] = self._scrape_detail_page(page, url, page_delay_ms)
                    except Exception:
                        results[url] = None
                    if progress_callback:
                        progress_callback(index, len(urls), index)
                return results
            finally:
                context.close()
                browser.close()

    def _scrape_detail_page(self, page: Page, url: str, page_delay_ms: int) -> SalonDetailEnrichment:
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(page_delay_ms)
        payload = page.evaluate(
            """
            () => {
              const find = (value, depth = 0) => {
                if (!value || depth > 8) return null;
                if (Array.isArray(value)) {
                  for (const item of value) {
                    const found = find(item, depth + 1);
                    if (found) return found;
                  }
                  return null;
                }
                if (typeof value !== 'object') return null;
                if (Array.isArray(value.service_categories)) {
                  return { service_categories: value.service_categories };
                }
                for (const nested of Object.values(value)) {
                  const found = find(nested, depth + 1);
                  if (found) return found;
                }
                return null;
              };
              return find(window.__NUXT__);
            }
            """
        )
        return parse_booksy_detail_payload(payload)

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
        base_urls = self._listing_base_urls(config)
        total_pages = config.pages * len(base_urls)
        completed_pages = 0
        salons: list[SalonIngestion] = []

        try:
            for base_url in base_urls:
                for current_page in range(1, config.pages + 1):
                    target_url = f"{base_url}/?businessesPage={current_page}"
                    page.goto(target_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(config.page_delay_ms)
                    page_salons = parse_booksy_listing_page(page.content())
                    salons.extend(page_salons)
                    completed_pages += 1
                    if progress_callback:
                        progress_callback(completed_pages, total_pages, len(salons))
        finally:
            context.close()
            browser.close()

        return salons

    def _listing_base_urls(self, config: ScraperConfig) -> list[str]:
        if config.base_url:
            return [config.base_url]

        base_urls = []
        for category in config.booksy_categories:
            if category not in BOOKSY_CATEGORY_URLS:
                raise ValueError(f"Unsupported Booksy category: {category}")
            base_urls.append(BOOKSY_CATEGORY_URLS[category])

        return base_urls or [BOOKSY_CATEGORY_URLS["hair"]]
