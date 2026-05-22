from __future__ import annotations

from backend.app.api.salons import _services_from_db, _sort_order


def test_services_from_db_returns_list_from_valid_json() -> None:
    assert _services_from_db('["Cut", "Color"]') == ["Cut", "Color"]


def test_services_from_db_returns_none_for_empty_invalid_or_non_list_json() -> None:
    assert _services_from_db(None) is None
    assert _services_from_db("") is None
    assert _services_from_db("{bad json") is None
    assert _services_from_db('{"service": "Cut"}') is None


def test_sort_order_builds_expected_name_direction() -> None:
    ascending = _sort_order("name", "asc")
    descending = _sort_order("name", "desc")

    assert "salons.name ASC" in str(ascending[0])
    assert "salons.name DESC" in str(descending[0])


def test_sort_order_keeps_null_prices_last() -> None:
    order = _sort_order("price", "asc")

    assert len(order) == 3
    assert "CASE" in str(order[0]).upper()
    assert "salons.price_range ASC" in str(order[1])
