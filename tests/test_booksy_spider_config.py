from __future__ import annotations

import pytest

from scraper.spiders.booksy import BooksySpider
from shared.schemas import ScraperConfig


def test_listing_base_urls_returns_hair_url() -> None:
    spider = BooksySpider()

    assert spider._listing_base_urls(ScraperConfig(booksy_categories=["hair"])) == [
        "https://booksy.com/pl-pl/s/fryzjer/3_warszawa"
    ]


def test_listing_base_urls_returns_nails_url() -> None:
    spider = BooksySpider()

    assert spider._listing_base_urls(ScraperConfig(booksy_categories=["nails"])) == [
        "https://booksy.com/pl-pl/s/paznokcie/3_warszawa"
    ]


def test_listing_base_urls_returns_both_urls_in_order() -> None:
    spider = BooksySpider()

    assert spider._listing_base_urls(ScraperConfig(booksy_categories=["hair", "nails"])) == [
        "https://booksy.com/pl-pl/s/fryzjer/3_warszawa",
        "https://booksy.com/pl-pl/s/paznokcie/3_warszawa",
    ]


def test_listing_base_urls_uses_explicit_base_url_for_manual_override() -> None:
    spider = BooksySpider()

    assert spider._listing_base_urls(
        ScraperConfig(base_url="https://booksy.com/custom", booksy_categories=["nails"])
    ) == ["https://booksy.com/custom"]


def test_listing_base_urls_rejects_unknown_category() -> None:
    spider = BooksySpider()

    with pytest.raises(ValueError, match="Unsupported Booksy category"):
        spider._listing_base_urls(ScraperConfig(booksy_categories=["tattoo"]))
