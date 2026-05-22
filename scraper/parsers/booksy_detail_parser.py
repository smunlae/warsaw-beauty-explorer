from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_PRICE_RE = re.compile(r"(\d+(?:[ \u00a0]\d{3})*(?:[,.]\d+)?)")


@dataclass(frozen=True)
class SalonDetailEnrichment:
    services_offered: list[str] | None = None
    price_range: str | None = None


def parse_booksy_detail_payload(payload: dict[str, Any] | None) -> SalonDetailEnrichment:
    if not payload:
        return SalonDetailEnrichment()

    categories = _find_service_categories(payload)
    services: list[str] = []
    prices: list[float] = []

    for category in categories:
        for service in _as_list(category.get("services")):
            if not isinstance(service, dict):
                continue
            name = _clean_string(service.get("name"))
            if name:
                services.append(name)
            for variant in _as_list(service.get("variants")):
                if not isinstance(variant, dict):
                    continue
                price = _parse_price(variant.get("service_price")) or _parse_price(variant.get("price"))
                if price is not None:
                    prices.append(price)

    return SalonDetailEnrichment(
        services_offered=_unique_preserve_order(services) or None,
        price_range=_format_price_range(prices),
    )


def _find_service_categories(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        value = payload.get("service_categories")
        if _looks_like_service_categories(value):
            return value
        for nested in payload.values():
            found = _find_service_categories(nested)
            if found:
                return found

    if isinstance(payload, list):
        for item in payload:
            found = _find_service_categories(item)
            if found:
                return found

    return []


def _looks_like_service_categories(value: object) -> bool:
    if not isinstance(value, list):
        return False
    return any(isinstance(item, dict) and isinstance(item.get("services"), list) for item in value)


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _clean_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _parse_price(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    text = value.replace("&nbsp;", " ").replace("\u00a0", " ")
    match = _PRICE_RE.search(text)
    if not match:
        return None

    normalized = match.group(1).replace(" ", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _format_price_range(prices: list[float]) -> str | None:
    if not prices:
        return None

    min_price = min(prices)
    max_price = max(prices)
    if min_price == max_price:
        return f"{_format_price(min_price)} PLN"
    return f"{_format_price(min_price)}-{_format_price(max_price)} PLN"


def _format_price(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    return unique
