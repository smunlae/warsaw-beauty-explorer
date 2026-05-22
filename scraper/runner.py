from __future__ import annotations

import argparse

from backend.app.core.config import settings
from scraper.pipeline import run_pipeline
from shared.schemas import ScraperConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Run salon data ingestion pipeline.")
    parser.add_argument("--source", default="booksy", help="Registered spider source name.")
    parser.add_argument("--pages", type=int, default=settings.booksy_default_pages, help="Number of listing pages to scrape.")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=settings.booksy_headless)
    parser.add_argument("--base-url", default=settings.booksy_base_url)
    args = parser.parse_args()

    config = ScraperConfig(
        source=args.source,
        pages=args.pages,
        headless=args.headless,
        base_url=args.base_url if args.source == "booksy" else None,
    )
    result = run_pipeline(config)
    print(
        f"source={result.source} collected={result.collected} "
        f"inserted={result.inserted} updated={result.updated}"
    )


if __name__ == "__main__":
    main()
