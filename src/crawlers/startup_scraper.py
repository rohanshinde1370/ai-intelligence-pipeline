import asyncio
import csv
import json
import re
from datetime import datetime, timezone

from playwright.async_api import async_playwright


SOURCE_URL = "https://www.ycombinator.com/companies"

OUTPUT_CSV = "startups.csv"
OUTPUT_JSON = "startups.json"


def clean_text(text):
    """Clean extra whitespace from extracted text."""
    if not text:
        return ""

    return re.sub(r"\s+", " ", text).strip()


async def scrape_yc():

    print("Starting YC startup scraper...")

    startups = {}

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page(
            viewport={
                "width": 1440,
                "height": 900
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0 Safari/537.36"
            )
        )

        print("Opening YC companies page...")

        response = await page.goto(
            SOURCE_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print(
            "Page status:",
            response.status if response else "Unknown"
        )

        print(
            "Page title:",
            await page.title()
        )

        # Give JavaScript time to load
        await page.wait_for_timeout(5000)

        previous_count = 0
        stable_rounds = 0

        # Try to load as many companies as possible
        for page_no in range(1, 101):

            print(
                f"Loading directory batch {page_no}/100..."
            )

            # Scroll to bottom
            await page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            await page.wait_for_timeout(1500)

            # Try common Load More buttons
            buttons = page.get_by_role(
                "button"
            )

            button_count = await buttons.count()

            clicked = False

            for i in range(button_count):

                try:

                    button = buttons.nth(i)

                    text = clean_text(
                        await button.inner_text()
                    ).lower()

                    if (
                        "load more" in text
                        or "show more" in text
                        or "more" == text
                    ):

                        if await button.is_visible():

                            await button.click()

                            print(
                                "Clicked:",
                                text
                            )

                            await page.wait_for_timeout(
                                2000
                            )

                            clicked = True

                            break

                except Exception:
                    continue

            # Count company links currently loaded
            current_count = await page.locator(
                'a[href^="/companies/"]'
            ).count()

            print(
                "Company links currently:",
                current_count
            )

            if current_count == previous_count:

                stable_rounds += 1

            else:

                stable_rounds = 0

            previous_count = current_count

            # If nothing new is loading for several rounds
            if stable_rounds >= 5 and not clicked:

                print(
                    "No additional companies detected."
                )

                break

        print("\nExtracting company records...")

        links = await page.locator(
            'a[href^="/companies/"]'
        ).all()

        print(
            "Company links found:",
            len(links)
        )

        collected_at = datetime.now(
            timezone.utc
        ).isoformat()

        for link in links:

            try:

                href = await link.get_attribute(
                    "href"
                )

                if not href:
                    continue

                # Remove query parameters
                href = href.split("?")[0]

                # Avoid invalid paths
                if href.rstrip("/") == "/companies":
                    continue

                if not href.startswith(
                    "/companies/"
                ):
                    continue

                company_url = (
                    "https://www.ycombinator.com"
                    + href
                )

                company_url = company_url.rstrip("/")

                # Extract text
                name = clean_text(
                    await link.inner_text()
                )

                if not name:
                    continue

                # YC cards contain extra information.
                # First line is normally the company name.
                lines = [
                    clean_text(x)
                    for x in name.split("\n")
                    if clean_text(x)
                ]

                entity_name = (
                    lines[0]
                    if lines
                    else name
                )

                # Avoid obvious navigation links
                if entity_name.lower() in {
                    "companies",
                    "jobs",
                    "people",
                    "cofounder matching",
                    "startup jobs",
                }:
                    continue

                startups[company_url] = {

                    "schemaVersion": "1.0",

                    "recordType": "STARTUP",

                    "source_name": "Y Combinator",

                    "source_url": company_url,

                    "entityName": entity_name,

                    "employeeCount": None,

                    "collectedAt": collected_at

                }

            except Exception:
                continue

        await browser.close()

    return list(
        startups.values()
    )


def save_csv(startups):

    fields = [
        "schemaVersion",
        "recordType",
        "source_name",
        "source_url",
        "entityName",
        "employeeCount",
        "collectedAt"
    ]

    with open(
        OUTPUT_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        writer.writerows(
            startups
        )

    print(
        f"CSV created: {OUTPUT_CSV}"
    )


def save_json(startups):

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            startups,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"JSON created: {OUTPUT_JSON}"
    )


async def main():

    startups = await scrape_yc()

    print(
        "\n======================================"
    )

    print(
        "Unique startups found:",
        len(startups)
    )

    print(
        "======================================"
    )

    if not startups:

        print(
            "No startup records found."
        )

        return

    print(
        "\n--- SAMPLE STARTUPS ---\n"
    )

    for i, startup in enumerate(
        startups[:20],
        start=1
    ):

        print(
            f"{i}. {startup['entityName']}"
        )

        print(
            "URL:",
            startup["source_url"]
        )

        print(
            "-" * 60
        )

    save_csv(startups)

    save_json(startups)

    print(
        "\n======================================"
    )

    print(
        "STARTUP SCRAPER COMPLETED"
    )

    print(
        "Total startups:",
        len(startups)
    )

    print(
        "======================================"
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )