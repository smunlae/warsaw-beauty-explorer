import json
import time
from playwright.sync_api import sync_playwright, Playwright
from selectolax.lexbor import LexborHTMLParser

def parse_and_extract(html_content):
    parser = LexborHTMLParser(html_content)
    script_tag = parser.css_first("script[type='application/ld+json'][data-hid='ld-json-0']")
    if not script_tag:
        print("No script tag, maybe we are blacklisted?")
        return []
    try:
        data = json.loads(script_tag.text())
    except Exception as e:
        print(e)
        return []

    items = data.get("itemListElement", [])
    page_salons = []
    print(f"Found {len(items)} salons on this page")

    for entry in items:
        salon = entry.get("item", {})
        name = salon.get("name")
        url = salon.get("url")

        address_info = salon.get("address", {})
        street = address_info.get("streetAddress")

        if street:
            parts = [p.strip() for p in street.split(",")]
            if len(parts) >= 2 and parts[-2].lower() == "warszawa":
                district = parts[-1]
                address = ", ".join(parts[:-2])
            else:
                district = "Warszawa"
                address = street
        else:
            address, district = "No info", "Warszawa"

        rating_info = salon.get("aggregateRating", {})
        rating = rating_info.get("ratingValue")   # Может быть None, если отзывов нет
        reviews_count = rating_info.get("reviewCount", 0)

        page_salons.append({
            "name": name,
            "address": address,
            "district": district,
            "url": url,
            "rating": float(rating) if rating else None,  # Приводим к числу для БД
            "reviews_count": int(reviews_count) if reviews_count else 0
        })

    return page_salons


def run(playwright: Playwright):
    chromium = playwright.chromium
    browser = chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 720}
    )
    page = context.new_page()
    base_url = "https://booksy.com/pl-pl/s/fryzjer/3_warszawa"
    all_salons = []
    total_pages = 2

    for current_page in range(1, total_pages+1):
        target_url = f"{base_url}/?businessesPage={current_page}"

        try:
            page.goto(target_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            html = page.content()
            salons_from_page = parse_and_extract(html)
            all_salons.extend(salons_from_page)
            time.sleep(1.5)
        except Exception as e:
            print(e)
            break

    browser.close()

    print(f"parsed {len(all_salons)} salons")

    for i, s in enumerate(all_salons):
        print(f"{i+1}. {s['name']} ({s['district']}) | Rating: {s['rating']} ({s['reviews_count']} reviews)")


with sync_playwright() as playwright:
    run(playwright)