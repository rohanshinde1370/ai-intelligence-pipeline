import asyncio
import csv
import json
import re
from datetime import datetime, timezone

from playwright.async_api import async_playwright


INPUT_CSV = "startups.csv"
OUTPUT_CSV = "products.csv"
OUTPUT_JSON = "products.json"

BASE_URL = "https://www.ycombinator.com"


def clean_text(text):
    if not text:
        return ""

    return re.sub(r"\s+", " ", text).strip()


def detect_pricing(text):
    text = text.lower()

    if "free trial" in text or "freemium" in text:
        return "FREEMIUM"

    if "free" in text:
        return "FREE"

    if "enterprise" in text:
        return "ENTERPRISE"

    if "pricing" in text or "subscription" in text:
        return "PAID"

    return None


async def extract_product(page, startup):

    url = startup["source_url"]

    try:

        response = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        if not response or response.status != 200:
            print("Failed:", url)
            return None

        await page.wait_for_timeout(1000)

        text = await page.locator(
            "body"
        ).inner_text()

        text = clean_text(text)

        if not text:
            return None

        # Keep useful source content
        description = text[:1000]

        pricing = detect_pricing(
            text
        )

        # --------------------------------------------------
        # PRODUCT RECORD
        # --------------------------------------------------

        product = {

            "schemaVersion": "1.0",

            "recordType": "PRODUCT",

            "source": {
                "name": "Y Combinator",
                "url": url
            },

            "content": {

                # Added productName
                "productName":
                    startup["entityName"],

                "startupName":
                    startup["entityName"],

                "productDescription":
                    description,

                "pricingModel":
                    pricing
            },

            "collectedAt":
                datetime.now(
                    timezone.utc
                ).isoformat()
        }

        return product

    except Exception as e:

        print(
            "Error:",
            url,
            "|",
            str(e)[:100]
        )

        return None


async def scrape_products():

    print(
        "Starting product extraction..."
    )

    with open(
        INPUT_CSV,
        "r",
        encoding="utf-8"
    ) as file:

        startups = list(
            csv.DictReader(file)
        )

    print(
        "Startup records loaded:",
        len(startups)
    )

    products = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page(
            viewport={
                "width": 1440,
                "height": 900
            }
        )

        for index, startup in enumerate(
            startups[:1000],
            start=1
        ):

            print(
                f"[{index}/1000] "
                f"{startup['entityName']}"
            )

            product = await extract_product(
                page,
                startup
            )

            if product:

                products.append(
                    product
                )

        await browser.close()

    return products


def save_files(products):

    # --------------------------------------------------
    # JSON
    # --------------------------------------------------

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            products,
            file,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------
    # CSV
    # --------------------------------------------------

    rows = []

    for product in products:

        rows.append({

            "schemaVersion":
                product["schemaVersion"],

            "recordType":
                product["recordType"],

            "source_name":
                product["source"]["name"],

            "source_url":
                product["source"]["url"],

            # Added productName
            "productName":
                product["content"]["productName"],

            "startupName":
                product["content"]["startupName"],

            "productDescription":
                product["content"]["productDescription"],

            "pricingModel":
                product["content"]["pricingModel"],

            "collectedAt":
                product["collectedAt"]
        })

    fields = [

        "schemaVersion",

        "recordType",

        "source_name",

        "source_url",

        "productName",

        "startupName",

        "productDescription",

        "pricingModel",

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
            rows
        )

    print(
        "CSV created:",
        OUTPUT_CSV
    )

    print(
        "JSON created:",
        OUTPUT_JSON
    )


async def main():

    products = await scrape_products()

    print(
        "\n======================================"
    )

    print(
        "PRODUCT EXTRACTION COMPLETED"
    )

    print(
        "Products found:",
        len(products)
    )

    print(
        "======================================"
    )

    if products:

        save_files(
            products
        )

        print(
            "\nSample products:\n"
        )

        for i, product in enumerate(
            products[:10],
            start=1
        ):

            print(
                f"{i}. "
                f"{product['content']['productName']}"
            )

            print(
                "Startup:",
                product["content"]["startupName"]
            )

            print(
                "URL:",
                product["source"]["url"]
            )

            print(
                "Pricing:",
                product["content"]["pricingModel"]
            )

            print(
                "Description:",
                product["content"][
                    "productDescription"
                ][:150]
            )

            print(
                "-" * 60
            )

    else:

        print(
            "No product records found."
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )