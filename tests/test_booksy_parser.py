from __future__ import annotations

import json

from scraper.parsers.booksy_parser import parse_booksy_listing_page


def _listing_html(items: list[dict]) -> str:
    payload = {"@context": "https://schema.org", "itemListElement": items}
    return f"""
    <html>
      <head>
        <script type="application/ld+json">{json.dumps(payload)}</script>
      </head>
    </html>
    """


def test_parse_booksy_listing_page_extracts_normalized_salon_fields() -> None:
    html = _listing_html(
        [
            {
                "item": {
                    "name": "Salon Test",
                    "url": "https://booksy.com/example",
                    "address": {"streetAddress": "ulica Testowa 1, Warszawa, Ochota"},
                    "aggregateRating": {"ratingValue": "4.91", "reviewCount": "123"},
                    "image": {
                        "url": "https://cdn.example.com/cover.jpg",
                    },
                },
            }
        ]
    )

    records = parse_booksy_listing_page(html)

    assert len(records) == 1
    assert records[0].source_name == "booksy"
    assert records[0].source_url == "https://booksy.com/example"
    assert records[0].name == "Salon Test"
    assert records[0].address == "ulica Testowa 1"
    assert records[0].district == "Ochota"
    assert records[0].rating == 4.91
    assert records[0].reviews_count == 123
    assert records[0].cover_image_url == "https://cdn.example.com/cover.jpg"


def test_parse_booksy_listing_page_supports_view_source_wrapper() -> None:
    escaped_html = _listing_html(
        [
            {
                "item": {
                    "name": "Nails Test",
                    "address": {"streetAddress": "ulica Paznokci 5, Warszawa, Wola"},
                    "aggregateRating": {},
                    "image": ["", "https://cdn.example.com/nails.jpg"],
                },
            }
        ]
    )
    wrapped = (
        "<html><body><table><tbody>"
        f"<tr><td class='line-content'>{escaped_html.replace('<', '&lt;').replace('>', '&gt;')}</td></tr>"
        "</tbody></table></body></html>"
    )

    records = parse_booksy_listing_page(wrapped)

    assert len(records) == 1
    assert records[0].name == "Nails Test"
    assert records[0].district == "Wola"
    assert records[0].rating is None
    assert records[0].reviews_count == 0
    assert records[0].cover_image_url == "https://cdn.example.com/nails.jpg"


def test_parse_booksy_listing_page_returns_empty_list_when_json_ld_missing() -> None:
    assert parse_booksy_listing_page("<html><body>No data</body></html>") == []
