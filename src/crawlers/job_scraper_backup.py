import asyncio
import aiohttp
import csv
import json
from datetime import datetime, timezone, timedelta


OUTPUT_CSV = "jobs.csv"
OUTPUT_JSON = "jobs.json"

REMOTIVE_API = (
    "https://remotive.com/api/remote-jobs"
)

HEADERS = {
    "User-Agent":
        "AI-Intelligence-Pipeline/1.0"
}


def parse_date(value):

    if not value:
        return None

    try:
        value = value.replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(
            value
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt

    except Exception:
        return None


def role_family(title):

    title = title.lower()

    if any(x in title for x in [
        "software",
        "developer",
        "engineer",
        "backend",
        "frontend",
        "full stack",
        "devops",
        "qa"
    ]):
        return "Engineering"

    if any(x in title for x in [
        "data",
        "machine learning",
        "ai ",
        "artificial intelligence",
        "ml "
    ]):
        return "Data & AI"

    if any(x in title for x in [
        "product manager",
        "product owner"
    ]):
        return "Product"

    if any(x in title for x in [
        "designer",
        "ux",
        "ui"
    ]):
        return "Design"

    if any(x in title for x in [
        "marketing",
        "growth"
    ]):
        return "Marketing"

    if any(x in title for x in [
        "sales",
        "business development"
    ]):
        return "Sales"

    return "Other"


async def fetch_remotive(session):

    print(
        "Fetching Remotive API..."
    )

    try:

        async with session.get(
            REMOTIVE_API,
            timeout=aiohttp.ClientTimeout(
                total=60
            )
        ) as response:

            print(
                "Remotive API status:",
                response.status
            )

            if response.status != 200:

                print(
                    "Remotive API failed."
                )

                return []

            data = await response.json()

            return data.get(
                "jobs",
                []
            )

    except Exception as e:

        print(
            "Remotive API error:",
            e
        )

        return []


async def main():

    print(
        "======================================"
    )

    print(
        "Starting Job Scraper..."
    )

    print(
        "24-hour freshness mode"
    )

    print(
        "======================================"
    )

    connector = aiohttp.TCPConnector(
        limit=10,
        family=2
    )

    async with aiohttp.ClientSession(
        headers=HEADERS,
        connector=connector
    ) as session:

        raw_jobs = await fetch_remotive(
            session
        )

    now = datetime.now(
        timezone.utc
    )

    cutoff = (
        now - timedelta(
            hours=24
        )
    )

    jobs = []
    seen = set()

    for item in raw_jobs:

        title = (
            item.get("title")
            or ""
        ).strip()

        company = (
            item.get("company_name")
            or ""
        ).strip()

        url = (
            item.get("url")
            or ""
        ).strip()

        date_text = (
            item.get("publication_date")
            or ""
        )

        published = parse_date(
            date_text
        )

        if not title:
            continue

        if not url:
            continue

        if not published:
            continue

        # STRICT 24-HOUR FILTER
        if published < cutoff:
            continue

        if published > now:
            continue

        key = url.lower()

        if key in seen:
            continue

        seen.add(key)

        category = (
            item.get("category")
            or ""
        )

        is_remote = True

        job = {

            "schemaVersion":
                "1.0",

            "recordType":
                "JOB",

            "source_name":
                "Remotive",

            "source_url":
                url,

            "content": {

                "company":
                    company,

                "title":
                    title,

                "date":
                    published.isoformat(),

                "is_remote":
                    is_remote,

                "role_family":
                    role_family(
                        title
                    ),

                "category":
                    category,

                "job_type":
                    item.get(
                        "job_type"
                    ),

                "candidate_required_location":
                    item.get(
                        "candidate_required_location"
                    )
            },

            "collectedAt":
                now.isoformat()
        }

        jobs.append(job)

    # =====================================================
    # SAVE CSV
    # =====================================================

    fields = [
        "schemaVersion",
        "recordType",
        "source_name",
        "source_url",
        "company",
        "title",
        "date",
        "is_remote",
        "role_family",
        "category",
        "job_type",
        "candidate_required_location",
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

        for job in jobs:

            content = job[
                "content"
            ]

            writer.writerow({

                "schemaVersion":
                    job["schemaVersion"],

                "recordType":
                    job["recordType"],

                "source_name":
                    job["source_name"],

                "source_url":
                    job["source_url"],

                "company":
                    content["company"],

                "title":
                    content["title"],

                "date":
                    content["date"],

                "is_remote":
                    content["is_remote"],

                "role_family":
                    content["role_family"],

                "category":
                    content["category"],

                "job_type":
                    content["job_type"],

                "candidate_required_location":
                    content[
                        "candidate_required_location"
                    ],

                "collectedAt":
                    job["collectedAt"]
            })

    # =====================================================
    # SAVE JSON
    # =====================================================

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            jobs,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print(
        "======================================"
    )

    print(
        "JOB SCRAPER COMPLETED"
    )

    print(
        "Fresh unique jobs:",
        len(jobs)
    )

    print(
        "CSV:",
        OUTPUT_CSV
    )

    print(
        "JSON:",
        OUTPUT_JSON
    )

    print(
        "======================================"
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )