import asyncio
import aiohttp
import csv
import json
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime


OUTPUT_CSV = "jobs.csv"
OUTPUT_JSON = "jobs.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


# --------------------------------------------------
# DATE PARSER
# --------------------------------------------------

def parse_date(value):

    if not value:
        return None

    value = value.strip()

    # ISO format
    try:
        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception:
        pass

    # RFC date
    try:
        dt = parsedate_to_datetime(
            value
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception:
        pass

    # Relative dates
    now = datetime.now(
        timezone.utc
    )

    match = re.search(
        r"(\d+)\s*(minute|minutes|min|mins)\s*ago",
        value,
        re.I
    )

    if match:

        minutes = int(
            match.group(1)
        )

        return now - timedelta(
            minutes=minutes
        )

    match = re.search(
        r"(\d+)\s*(hour|hours|hr|hrs)\s*ago",
        value,
        re.I
    )

    if match:

        hours = int(
            match.group(1)
        )

        return now - timedelta(
            hours=hours
        )

    match = re.search(
        r"(\d+)\s*(day|days)\s*ago",
        value,
        re.I
    )

    if match:

        days = int(
            match.group(1)
        )

        return now - timedelta(
            days=days
        )

    return None


# --------------------------------------------------
# 24 HOUR CHECK
# --------------------------------------------------

def is_fresh(dt):

    if dt is None:
        return False

    now = datetime.now(
        timezone.utc
    )

    age = (
        now - dt
    ).total_seconds()

    return (
        0 <= age <= 86400
    )


# --------------------------------------------------
# ROLE FAMILY
# --------------------------------------------------

def get_role_family(title):

    title_lower = title.lower()

    if any(
        word in title_lower
        for word in [
            "software engineer",
            "software developer",
            "developer",
            "backend",
            "frontend",
            "full stack",
            "fullstack",
            "devops",
            "qa engineer"
        ]
    ):
        return "Engineering"

    if any(
        word in title_lower
        for word in [
            "data scientist",
            "data analyst",
            "data engineer",
            "machine learning",
            "ml engineer",
            "ai engineer"
        ]
    ):
        return "Data & AI"

    if any(
        word in title_lower
        for word in [
            "product manager",
            "product owner"
        ]
    ):
        return "Product"

    if any(
        word in title_lower
        for word in [
            "designer",
            "ux",
            "ui"
        ]
    ):
        return "Design"

    if any(
        word in title_lower
        for word in [
            "marketing",
            "growth"
        ]
    ):
        return "Marketing"

    return "Other"


# --------------------------------------------------
# REMOTE DETECTION
# --------------------------------------------------

def is_remote(title, description=""):

    text = (
        title + " " + description
    ).lower()

    remote_words = [
        "remote",
        "work from home",
        "wfh",
        "distributed"
    ]

    return any(
        word in text
        for word in remote_words
    )


# --------------------------------------------------
# REMOTE OK
# --------------------------------------------------

async def scrape_remote_ok(session):

    url = "https://remoteok.com/api"

    print(
        "\nRemote OK..."
    )

    try:

        async with session.get(
            url,
            timeout=30
        ) as response:

            print(
                "HTTP:",
                response.status
            )

            if response.status != 200:
                return []

            data = await response.json(
                content_type=None
            )

            jobs = []

            for item in data:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                title = item.get(
                    "position"
                )

                company = item.get(
                    "company"
                )

                job_url = item.get(
                    "url"
                )

                date_value = (
                    item.get("date")
                    or item.get("epoch")
                )

                if not title or not job_url:
                    continue

                if not job_url.startswith(
                    "http"
                ):
                    job_url = (
                        "https://remoteok.com"
                        + job_url
                    )

                published = None

                if isinstance(
                    date_value,
                    (int, float)
                ):

                    published = datetime.fromtimestamp(
                        date_value,
                        timezone.utc
                    )

                else:

                    published = parse_date(
                        str(date_value)
                    )

                if not is_fresh(
                    published
                ):
                    continue

                description = item.get(
                    "description",
                    ""
                )

                jobs.append({

                    "schemaVersion":
                        "1.0",

                    "recordType":
                        "JOB",

                    "company":
                        company,

                    "date":
                        published.isoformat(),

                    "is_remote":
                        True,

                    "role_family":
                        get_role_family(
                            title
                        ),

                    "title":
                        title,

                    "source_name":
                        "Remote OK",

                    "source_url":
                        job_url,

                    "collectedAt":
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                })

            print(
                "Fresh jobs:",
                len(jobs)
            )

            return jobs

    except Exception as e:

        print(
            "Remote OK error:",
            e
        )

        return []


# --------------------------------------------------
# JOBICY API
# --------------------------------------------------

async def scrape_jobicy(session):

    url = (
        "https://jobicy.com/"
        "api/v2/remote-jobs"
    )

    print(
        "\nJobicy..."
    )

    try:

        async with session.get(
            url,
            timeout=30
        ) as response:

            print(
                "HTTP:",
                response.status
            )

            if response.status != 200:
                return []

            data = await response.json(
                content_type=None
            )

            jobs = []

            for item in data.get(
                "jobs",
                []
            ):

                title = item.get(
                    "jobTitle"
                )

                company = item.get(
                    "companyName"
                )

                job_url = item.get(
                    "url"
                )

                date_value = (
                    item.get(
                        "pubDate"
                    )
                    or item.get(
                        "date"
                    )
                )

                if not title or not job_url:
                    continue

                published = parse_date(
                    str(date_value)
                )

                if not is_fresh(
                    published
                ):
                    continue

                jobs.append({

                    "schemaVersion":
                        "1.0",

                    "recordType":
                        "JOB",

                    "company":
                        company,

                    "date":
                        published.isoformat(),

                    "is_remote":
                        True,

                    "role_family":
                        get_role_family(
                            title
                        ),

                    "title":
                        title,

                    "source_name":
                        "Jobicy",

                    "source_url":
                        job_url,

                    "collectedAt":
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                })

            print(
                "Fresh jobs:",
                len(jobs)
            )

            return jobs

    except Exception as e:

        print(
            "Jobicy error:",
            e
        )

        return []


# --------------------------------------------------
# MAIN
# --------------------------------------------------

async def main():

    print(
        "======================================"
    )

    print(
        "Starting Job Scraper..."
    )

    print(
        "Requirement: 24-hour fresh jobs"
    )

    print(
        "======================================"
    )

    connector = aiohttp.TCPConnector(
        family=2,
        ssl=False
    )

    async with aiohttp.ClientSession(
        connector=connector,
        headers=HEADERS
    ) as session:

        results = await asyncio.gather(

            scrape_remote_ok(
                session
            ),

            scrape_jobicy(
                session
            ),

            return_exceptions=True
        )

    all_jobs = []

    for result in results:

        if isinstance(
            result,
            list
        ):

            all_jobs.extend(
                result
            )

    # --------------------------------------------------
    # DEDUPLICATION
    # --------------------------------------------------

    unique = {}

    for job in all_jobs:

        url = job.get(
            "source_url"
        )

        if url:
            unique[url] = job

    jobs = list(
        unique.values()
    )

    # --------------------------------------------------
    # SAVE CSV
    # --------------------------------------------------

    fields = [
        "schemaVersion",
        "recordType",
        "company",
        "date",
        "is_remote",
        "role_family",
        "title",
        "source_name",
        "source_url",
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
            jobs
        )

    # --------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------

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

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------

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