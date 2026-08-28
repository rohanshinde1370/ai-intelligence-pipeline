import asyncio
import csv
import json
from datetime import datetime, timezone
from playwright.async_api import async_playwright


SOURCE_URL = "https://www.ycombinator.com/companies"

OUTPUT_CSV = "startups.csv"
OUTPUT_JSON = "startups.json"


async def main():

    print("Starting YC startup scraper...")

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        print("Opening YC companies page...")

        try:

            response = await page.goto(
                SOURCE_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            print(
                "Page status:",
                response.status if response else None
            )

        except Exception as e:

            print(
                "Page loading error:",
                repr(e)
            )

            await browser.close()
            return

        # Give JavaScript time to render
        await page.wait_for_timeout(5000)

        print(
            "Page title:",
            await page.title()
        )

        startups = {}

        # Scroll several times so dynamically loaded
        # companies have a chance to appear.
        for i in range(20):

            print(
                f"Scrolling page {i + 1}/20..."
            )

            await page.mouse.wheel(
                0,
                5000
            )

            await page.wait_for_timeout(
                1000
            )

        # Extract company links from rendered DOM
        links = await page.locator(
            'a[href^="/companies/"]'
        ).all()

        print(
            "Company links found:",
            len(links)
        )

        for link in links:

            try:

                href = await link.get_attribute(
                    "href"
                )

                name = (
                    await link.inner_text()
                ).strip()

                if not href or not name:
                    continue

                # Remove query parameters
                href = href.split("?")[0]

                # Avoid invalid company URL
                if href == "/companies/":
                    continue

                company_url = (
                    "https://www.ycombinator.com"
                    + href
                )

                # Deduplicate by URL
                startups[company_url] = {

                    "schemaVersion": "1.0",

                    "recordType": "STARTUP",

                    "source_name": "Y Combinator",

                    "source_url": company_url,

                    "entityName": " ".join(
                        name.split()
                    ),

                    "employeeCount": None,

                    "collectedAt":
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                }

            except Exception:
                continue

        records = list(
            startups.values()
        )

        print(
            "\nUnique startups found:",
            len(records)
        )

        if not records:

            print(
                "No startups found."
            )

            await browser.close()
            return

        # -------------------------
        # Save CSV
        # -------------------------

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
            writer.writerows(records)

        print(
            f"CSV created: {OUTPUT_CSV}"
        )

        # -------------------------
        # Save JSON
        # -------------------------

        with open(
            OUTPUT_JSON,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                records,
                file,
                indent=2,
                ensure_ascii=False
            )

        print(
            f"JSON created: {OUTPUT_JSON}"
        )

        # -------------------------
        # Sample
        # -------------------------

        print(
            "\n--- SAMPLE STARTUPS ---\n"
        )

        for i, startup in enumerate(
            records[:10],
            start=1
        ):

            print(
                f"{i}. "
                f"{startup['entityName']}"
            )

            print(
                "URL:",
                startup["source_url"]
            )

            print("-" * 60)

        await browser.close()

    print(
        "\n======================================"
    )

    print(
        "STARTUP SCRAPER COMPLETED"
    )

    print(
        f"Total startups: {len(records)}"
    )

    print(
        "======================================"
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )