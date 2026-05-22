from __future__ import annotations

from scraper.parsers.booksy_detail_parser import parse_booksy_detail_payload


def test_parse_booksy_detail_payload_extracts_services_and_price_range() -> None:
    payload = {
        "nested": {
            "service_categories": [
                {
                    "services": [
                        {
                            "name": " Manicure hybrydowy ",
                            "variants": [
                                {"service_price": "120 PLN"},
                                {"price": "150,50 zł"},
                            ],
                        },
                        {
                            "name": "manicure hybrydowy",
                            "variants": [{"service_price": "100 PLN"}],
                        },
                        {
                            "name": "Pedicure",
                            "variants": [{"service_price": "1 200 PLN"}],
                        },
                    ]
                }
            ]
        }
    }

    result = parse_booksy_detail_payload(payload)

    assert result.services_offered == ["Manicure hybrydowy", "Pedicure"]
    assert result.price_range == "100-1200 PLN"


def test_parse_booksy_detail_payload_handles_missing_data() -> None:
    result = parse_booksy_detail_payload({"service_categories": []})

    assert result.services_offered is None
    assert result.price_range is None


def test_parse_booksy_detail_payload_formats_single_decimal_price() -> None:
    payload = {
        "service_categories": [
            {
                "services": [
                    {
                        "name": "Cut",
                        "variants": [{"service_price": "99,90 PLN"}],
                    }
                ]
            }
        ]
    }

    result = parse_booksy_detail_payload(payload)

    assert result.services_offered == ["Cut"]
    assert result.price_range == "99.9 PLN"
