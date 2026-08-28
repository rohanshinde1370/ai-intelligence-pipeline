import asyncio
import aiohttp
import ssl
import certifi
import socket
import csv
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


ARXIV_API = "https://export.arxiv.org/api/query"
GITHUB_API = "https://api.github.com/repos"

OUTPUT_CSV = "research_papers.csv"
OUTPUT_JSON = "research_papers.json"

TARGET = 1000
BATCH_SIZE = 100

NS = {
    "atom": "http://www.w3.org/2005/Atom"
}


# =========================================================
# SSL CONFIGURATION
# =========================================================

def create_ssl_context():

    return ssl.create_default_context(
        cafile=certifi.where()
    )


# =========================================================
# EXTRACT GITHUB REPOSITORY
# =========================================================

def github_repo_from_text(text):

    if not text:
        return None

    pattern = (
        r"https?://github\.com/"
        r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
    )

    match = re.search(
        pattern,
        text
    )

    if not match:
        return None

    repo = match.group(1)

    repo = repo.rstrip("/")
    repo = repo.split("?")[0]
    repo = repo.split("#")[0]

    return repo


# =========================================================
# PARSE ARXIV ENTRY
# =========================================================

def parse_entry(entry):

    title = entry.findtext(
        "atom:title",
        "",
        NS
    ).strip()

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    summary = entry.findtext(
        "atom:summary",
        "",
        NS
    ).strip()

    summary = re.sub(
        r"\s+",
        " ",
        summary
    )

    published = entry.findtext(
        "atom:published",
        "",
        NS
    ).strip()

    updated = entry.findtext(
        "atom:updated",
        "",
        NS
    ).strip()

    authors = []

    for author in entry.findall(
        "atom:author",
        NS
    ):

        name = author.findtext(
            "atom:name",
            "",
            NS
        ).strip()

        if name:
            authors.append(name)

    paper_url = ""

    for link in entry.findall(
        "atom:link",
        NS
    ):

        href = link.attrib.get(
            "href",
            ""
        )

        if "/abs/" in href:

            paper_url = href

            break

    github_repo = github_repo_from_text(
        summary
    )

    github_url = None

    if github_repo:

        github_url = (
            "https://github.com/"
            + github_repo
        )

    return {

        "schemaVersion": "1.0",

        "recordType": "RESEARCH_PAPER",

        "source_name": "arXiv",

        "source_url": paper_url,

        "title": title,

        "authors": authors,

        "paper_url": paper_url,

        "github_url": github_url,

        "github_stars": None,

        "published_date": published,

        "updated_date": updated,

        "collectedAt":
            datetime.now(
                timezone.utc
            ).isoformat()
    }


# =========================================================
# FETCH ARXIV
# =========================================================

async def fetch_arxiv(
    session,
    start
):

    params = {

        "search_query":
            "cat:cs.AI",

        "start":
            start,

        "max_results":
            BATCH_SIZE,

        "sortBy":
            "submittedDate",

        "sortOrder":
            "descending"
    }

    try:

        async with session.get(
            ARXIV_API,
            params=params,
            timeout=aiohttp.ClientTimeout(
                total=90
            )
        ) as response:

            print(
                "arXiv status:",
                response.status
            )

            if response.status != 200:

                print(
                    "arXiv request failed"
                )

                return []

            xml_data = await response.text()

            root = ET.fromstring(
                xml_data
            )

            entries = root.findall(
                "atom:entry",
                NS
            )

            papers = []

            for entry in entries:

                paper = parse_entry(
                    entry
                )

                if paper["paper_url"]:

                    papers.append(
                        paper
                    )

            return papers

    except Exception as e:

        print(
            "arXiv error:",
            e
        )

        return []


# =========================================================
# GITHUB STAR COUNT
# =========================================================

async def get_github_stars(
    session,
    github_url,
    semaphore
):

    if not github_url:

        return None

    repo = github_url.replace(
        "https://github.com/",
        ""
    )

    api_url = (
        f"{GITHUB_API}/{repo}"
    )

    async with semaphore:

        try:

            async with session.get(
                api_url,
                timeout=aiohttp.ClientTimeout(
                    total=30
                )
            ) as response:

                if response.status == 200:

                    data = await response.json()

                    return data.get(
                        "stargazers_count"
                    )

                if response.status in (
                    403,
                    429
                ):

                    print(
                        "GitHub rate limit reached"
                    )

                    return None

                return None

        except Exception as e:

            print(
                "GitHub error:",
                e
            )

            return None


# =========================================================
# SAVE CSV + JSON
# =========================================================

def save_files(papers):

    rows = []

    for paper in papers:

        rows.append({

            "schemaVersion":
                paper["schemaVersion"],

            "recordType":
                paper["recordType"],

            "source_name":
                paper["source_name"],

            "source_url":
                paper["source_url"],

            "title":
                paper["title"],

            "authors":
                json.dumps(
                    paper["authors"],
                    ensure_ascii=False
                ),

            "paper_url":
                paper["paper_url"],

            "github_url":
                paper["github_url"],

            "github_stars":
                paper["github_stars"],

            "published_date":
                paper["published_date"],

            "collectedAt":
                paper["collectedAt"]
        })

    fields = [

        "schemaVersion",
        "recordType",
        "source_name",
        "source_url",
        "title",
        "authors",
        "paper_url",
        "github_url",
        "github_stars",
        "published_date",
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

        writer.writerows(rows)

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            papers,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        "CSV created:",
        OUTPUT_CSV
    )

    print(
        "JSON created:",
        OUTPUT_JSON
    )


# =========================================================
# MAIN
# =========================================================

async def main():

    print(
        "======================================"
    )

    print(
        "Starting Research Paper Scraper..."
    )

    print(
        "Target:",
        TARGET
    )

    print(
        "======================================"
    )

    ssl_context = create_ssl_context()

    connector = aiohttp.TCPConnector(

        ssl=ssl_context,

        family=socket.AF_INET,

        limit=10
    )

    headers = {

        "User-Agent":
            "AI-Intelligence-Pipeline/1.0",

        "Accept":
            "application/atom+xml"
    }

    async with aiohttp.ClientSession(

        connector=connector,

        headers=headers

    ) as session:

        papers = []

        seen_urls = set()

        start = 0

        # -----------------------------------------
        # FETCH 1000 PAPERS
        # -----------------------------------------

        while len(papers) < TARGET:

            print()

            print(
                f"Fetching papers "
                f"{start} - "
                f"{start + BATCH_SIZE}..."
            )

            batch = await fetch_arxiv(
                session,
                start
            )

            if not batch:

                print(
                    "No more papers received."
                )

                break

            for paper in batch:

                url = paper[
                    "paper_url"
                ]

                if url in seen_urls:

                    continue

                seen_urls.add(url)

                papers.append(
                    paper
                )

                if len(papers) >= TARGET:

                    break

            print(
                "Unique papers:",
                len(papers)
            )

            start += BATCH_SIZE

            await asyncio.sleep(3)

        # -----------------------------------------
        # GITHUB STARS
        # -----------------------------------------

        github_papers = [

            paper

            for paper in papers

            if paper["github_url"]

        ]

        print()

        print(
            "Papers with GitHub URLs:",
            len(github_papers)
        )

        semaphore = asyncio.Semaphore(
            5
        )

        tasks = []

        for paper in github_papers:

            tasks.append(

                get_github_stars(

                    session,

                    paper["github_url"],

                    semaphore

                )

            )

        if tasks:

            stars = await asyncio.gather(
                *tasks
            )

            for paper, star_count in zip(
                github_papers,
                stars
            ):

                paper[
                    "github_stars"
                ] = star_count

        # -----------------------------------------
        # SAVE
        # -----------------------------------------

        save_files(
            papers
        )

    print()

    print(
        "======================================"
    )

    print(
        "RESEARCH PAPER SCRAPER COMPLETED"
    )

    print(
        "Total papers:",
        len(papers)
    )

    print(
        "======================================"
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )