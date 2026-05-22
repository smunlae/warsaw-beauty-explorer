from __future__ import annotations

import html
import json
from typing import Any

from selectolax.lexbor import LexborHTMLParser
from shared.schemas import SalonIngestion


def parse_booksy_listing_page(html_content: str) -> list[SalonIngestion]:
    parser = LexborHTMLParser(_extract_source_html(html_content))
    data = _find_listing_json_ld(parser)
    if not data:
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


def _extract_source_html(html_content: str) -> str:
    parser = LexborHTMLParser(html_content)
    source_lines = parser.css("td.line-content")
    if not source_lines:
        return html_content
    return html.unescape("\n".join(line.text() for line in source_lines))


def _find_listing_json_ld(parser: LexborHTMLParser) -> dict[str, Any] | None:
    for script_tag in parser.css("script[type='application/ld+json']"):
        try:
            data = json.loads(script_tag.text())
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and isinstance(data.get("itemListElement"), list):
            return data
    return None


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
        cover_image_url=_parse_image_url(salon.get("image")),
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


def _parse_image_url(value: object) -> str | None:
    if isinstance(value, str):
        return _clean_optional_string(value)

    if isinstance(value, list):
        for item in value:
            parsed = _parse_image_url(item)
            if parsed:
                return parsed
        return None

    if isinstance(value, dict):
        for key in ("url", "image", "contentUrl"):
            parsed = _parse_image_url(value.get(key))
            if parsed:
                return parsed

    return None
