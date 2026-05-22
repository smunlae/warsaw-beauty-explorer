from __future__ import annotations

import json
from typing import Any

from selectolax.lexbor import LexborHTMLParser
from shared.schemas import SalonIngestion


def parse_booksy_listing_page(html_content: str) -> list[SalonIngestion]:
    parser = LexborHTMLParser(html_content)
    script_tag = parser.css_first("script[type='application/ld+json'][data-hid='ld-json-0']")
    if not script_tag:
        return []

    try:
        data = json.loads(script_tag.text())
    except json.JSONDecodeError:
        return []

    items = data.get("itemListElement", [])
    if not isinstance(items, list):
        return []

    salons: list[SalonIngestion] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        salon = entry.get("item", {})
        if not isinstance(salon, dict):
            continue

        parsed = _parse_salon_item(salon)
        if parsed:
            salons.append(parsed)

    return salons


def _parse_salon_item(salon: dict[str, Any]) -> SalonIngestion | None:
    name = salon.get("name")
    if not isinstance(name, str) or not name.strip():
        return None

    address, district = _parse_address(salon.get("address"))
    rating, reviews_count = _parse_rating(salon.get("aggregateRating"))

    return SalonIngestion(
        source_name="booksy",
        source_url=_clean_optional_string(salon.get("url")),
        name=name,
        address=address,
        district=district,
        rating=rating,
        reviews_count=reviews_count,
    )


def _parse_address(address_info: object) -> tuple[str, str]:
    if not isinstance(address_info, dict):
        return "No info", "Warszawa"

    street = address_info.get("streetAddress")
    if not isinstance(street, str) or not street.strip():
        return "No info", "Warszawa"

    parts = [part.strip() for part in street.split(",") if part.strip()]
    if len(parts) >= 2 and parts[-2].lower() == "warszawa":
        district = parts[-1]
        address = ", ".join(parts[:-2]) or street
        return address, district

    return street, "Warszawa"


def _parse_rating(rating_info: object) -> tuple[float | None, int]:
    if not isinstance(rating_info, dict):
        return None, 0

    raw_rating = rating_info.get("ratingValue")
    raw_reviews = rating_info.get("reviewCount", 0)

    rating = None
    if raw_rating not in (None, ""):
        try:
            rating = float(raw_rating)
        except (TypeError, ValueError):
            rating = None

    try:
        reviews_count = int(raw_reviews or 0)
    except (TypeError, ValueError):
        reviews_count = 0

    return rating, reviews_count


def _clean_optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None
