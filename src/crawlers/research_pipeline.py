import aiohttp
import asyncio
import ssl
import certifi
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timezone


ARXIV_API = "https://export.arxiv.org/api/query"
GITHUB_API = "https://api.github.com/search/repositories"

TOTAL_PAPERS = 1000
BATCH_SIZE = 100

NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom"
}


def create_ssl_context():
    return ssl.create_default_context(
        cafile=certifi.where()
    )


async def get_arxiv_batch(session, start, batch_size):

    params = {
        "search_query": "cat:cs.AI",
        "start": start,
        "max_results": batch_size,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    for attempt in range(3):

        try:

            async with session.get(
                ARXIV_API,
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:

                print(
                    f"arXiv batch {start}-{start + batch_size} "
                    f"Status: {response.status}"
                )

                if response.status == 200:

                    xml_data = await response.text()

                    root = ET.fromstring(
                        xml_data
                    )

                    return root.findall(
                        "atom:entry",
                        NAMESPACES
                    )

                print(
                    "arXiv request failed. Retry:",
                    attempt + 1
                )

        except Exception as e:

            print(
                "arXiv error:",
                e
            )

        await asyncio.sleep(
            2 ** attempt
        )

    return []


async def search_github(session, title):

    # Use important words from title
    keywords = " ".join(
        title.split()[:6]
    )

    params = {
        "q": keywords,
        "sort": "stars",
        "order": "desc",
        "per_page": 5
    }

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-Intelligence-Pipeline"
    }

    for attempt in range(3):

        try:

            async with session.get(
                GITHUB_API,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:

                if response.status == 200:

                    data = await response.json()

                    repositories = data.get(
                        "items",
                        []
                    )

                    if not repositories:
                        return None, None

                    repo = repositories[0]

                    return (
                        repo.get("html_url"),
                        repo.get("stargazers_count")
                    )

                elif response.status == 403:

                    print(
                        "GitHub rate limit reached. Waiting..."
                    )

                    await asyncio.sleep(
                        10 * (attempt + 1)
                    )

                elif response.status == 429:

                    print(
                        "GitHub 429 rate limit. Waiting..."
                    )

                    await asyncio.sleep(
                        10 * (attempt + 1)
                    )

                else:

                    print(
                        "GitHub status:",
                        response.status
                    )

        except Exception as e:

            print(
                "GitHub error:",
                e
            )

        await asyncio.sleep(
            2 ** attempt
        )

    return None, None


def parse_entry(entry):

    # -------------------------
    # Title
    # -------------------------

    title_element = entry.find(
        "atom:title",
        NAMESPACES
    )

    title = ""

    if title_element is not None:

        title = " ".join(
            title_element.text.split()
        )

    # -------------------------
    # Authors
    # -------------------------

    authors = []

    for author in entry.findall(
        "atom:author",
        NAMESPACES
    ):

        name_element = author.find(
            "atom:name",
            NAMESPACES
        )

        if name_element is not None:

            authors.append(
                name_element.text.strip()
            )

    # -------------------------
    # Paper URL
    # -------------------------

    id_element = entry.find(
        "atom:id",
        NAMESPACES
    )

    paper_url = None

    if id_element is not None:

        paper_url = id_element.text.strip()

    # -------------------------
    # Published Date
    # -------------------------

    published_element = entry.find(
        "atom:published",
        NAMESPACES
    )

    published_date = None

    if published_element is not None:

        published_date = (
            published_element.text.strip()
        )

    # -------------------------
    # Updated Date
    # -------------------------

    updated_element = entry.find(
        "atom:updated",
        NAMESPACES
    )

    updated_date = None

    if updated_element is not None:

        updated_date = (
            updated_element.text.strip()
        )

    return {
        "title": title,
        "authors": ", ".join(authors),
        "paper_url": paper_url,
        "published_date": published_date,
        "updated_date": updated_date
    }


async def main():

    ssl_context = create_ssl_context()

    connector = aiohttp.TCPConnector(
        ssl=ssl_context
    )

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        # ==================================
        # STEP 1: Collect arXiv papers
        # ==================================

        all_entries = []

        for start in range(
            0,
            TOTAL_PAPERS,
            BATCH_SIZE
        ):

            remaining = (
                TOTAL_PAPERS - start
            )

            current_batch = min(
                BATCH_SIZE,
                remaining
            )

            entries = await get_arxiv_batch(
                session,
                start,
                current_batch
            )

            if not entries:
                break

            all_entries.extend(
                entries
            )

            print(
                f"Collected papers: "
                f"{len(all_entries)}/{TOTAL_PAPERS}"
            )

            # Be polite to arXiv
            await asyncio.sleep(3)

        print(
            "\nTotal papers collected:",
            len(all_entries)
        )

        # ==================================
        # STEP 2: GitHub lookup
        # ==================================

        rows = []

        for i, entry in enumerate(
            all_entries,
            start=1
        ):

            paper = parse_entry(entry)

            print(
                f"\n[{i}/{len(all_entries)}] "
                f"{paper['title']}"
            )

            github_url, github_stars = (
                await search_github(
                    session,
                    paper["title"]
                )
            )

            print(
                "GitHub URL:",
                github_url
            )

            print(
                "GitHub Stars:",
                github_stars
            )

            collected_at = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            rows.append({

                "schemaVersion":
                    "1.0",

                "recordType":
                    "RESEARCH_PAPER",

                "title":
                    paper["title"],

                "authors":
                    paper["authors"],

                "paper_url":
                    paper["paper_url"],

                "github_url":
                    github_url,

                "github_stars":
                    github_stars,

                "published_date":
                    paper["published_date"],

                "updated_date":
                    paper["updated_date"],

                "source":
                    "arXiv",

                "collected_at":
                    collected_at
            })

            # Prevent GitHub rate pressure
            await asyncio.sleep(1)

        # ==================================
        # STEP 3: Save CSV
        # ==================================

        filename = "research_papers.csv"

        fieldnames = [

            "schemaVersion",

            "recordType",

            "title",

            "authors",

            "paper_url",

            "github_url",

            "github_stars",

            "published_date",

            "updated_date",

            "source",

            "collected_at"
        ]

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            writer.writeheader()

            writer.writerows(
                rows
            )

        print(
            "\n======================================"
        )

        print(
            "RESEARCH PIPELINE COMPLETED"
        )

        print(
            "Papers:",
            len(rows)
        )

        print(
            "CSV:",
            filename
        )

        print(
            "======================================"
        )


asyncio.run(
    main()
)
