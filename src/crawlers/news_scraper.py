import asyncio
import aiohttp
import csv
import json
import re
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin


OUTPUT_CSV = "news.csv"
OUTPUT_JSON = "news.json"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml,application/xml,text/xml,text/html",
    "Accept-Language": "en-US,en;q=0.9",
}


# ==================================================
# 5 AI NEWS SOURCES
# ==================================================

NEWS_SOURCES = {

    "TechCrunch AI":
        "https://techcrunch.com/category/artificial-intelligence/feed/",

    "VentureBeat AI":
        "https://venturebeat.com/category/ai/feed/",

    "The Verge AI":
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",

    "WIRED AI":
        "https://www.wired.com/feed/tag/ai/latest/rss",

    "MIT Technology Review AI":
        "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
}


# ==================================================
# DATE PARSER
# ==================================================

def parse_date(value):

    if not value:
        return None

    value = str(value).strip()

    # ISO-8601
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

    # RFC / RSS date
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

    # Relative: "2 hours ago"
    now = datetime.now(
        timezone.utc
    )

    match = re.search(
        r"(\d+)\s*(minute|minutes|min|mins)\s*ago",
        value,
        re.I
    )

    if match:

        return now - timedelta(
            minutes=int(
                match.group(1)
            )
        )

    match = re.search(
        r"(\d+)\s*(hour|hours|hr|hrs)\s*ago",
        value,
        re.I
    )

    if match:

        return now - timedelta(
            hours=int(
                match.group(1)
            )
        )

    match = re.search(
        r"(\d+)\s*(day|days)\s*ago",
        value,
        re.I
    )

    if match:

        return now - timedelta(
            days=int(
                match.group(1)
            )
        )

    return None


# ==================================================
# STRICT 24-HOUR CHECK
# ==================================================

def is_fresh(published):

    if published is None:
        return False

    now = datetime.now(
        timezone.utc
    )

    age = (
        now - published
    ).total_seconds()

    return 0 <= age <= 86400


# ==================================================
# HTML CLEANING
# ==================================================

def clean_text(text):

    if not text:
        return ""

    soup = BeautifulSoup(
        text,
        "html.parser"
    )

    return " ".join(
        soup.get_text(
            " ",
            strip=True
        ).split()
    )


# ==================================================
# FULL ARTICLE TEXT
# ==================================================

async def fetch_article_text(
    session,
    url
):

    try:

        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(
                total=20
            )
        ) as response:

            if response.status != 200:
                return ""

            html = await response.text(
                errors="ignore"
            )

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            # Remove unwanted elements
            for tag in soup([
                "script",
                "style",
                "noscript",
                "nav",
                "footer",
                "header",
                "form",
                "aside"
            ]):

                tag.decompose()

            article = soup.find(
                "article"
            )

            if article:

                text = article.get_text(
                    " ",
                    strip=True
                )

            else:

                paragraphs = soup.find_all(
                    "p"
                )

                text = " ".join(
                    p.get_text(
                        " ",
                        strip=True
                    )
                    for p in paragraphs
                )

            return clean_text(
                text
            )

    except Exception:

        return ""


# ==================================================
# RSS PARSER
# ==================================================

def parse_rss(xml_data):

    records = []

    try:

        root = ET.fromstring(
            xml_data
        )

    except Exception as e:

        print(
            "RSS XML error:",
            e
        )

        return []

    # RSS
    for item in root.findall(
        ".//item"
    ):

        title = item.findtext(
            "title"
        )

        link = item.findtext(
            "link"
        )

        description = item.findtext(
            "description"
        )

        pub_date = item.findtext(
            "pubDate"
        )

        if not link:

            # Some feeds use atom link
            link_node = item.find(
                "{http://www.w3.org/2005/Atom}link"
            )

            if link_node is not None:

                link = link_node.attrib.get(
                    "href"
                )

        records.append({

            "title": clean_text(
                title
            ),

            "url": (
                link.strip()
                if link
                else ""
            ),

            "description":
                clean_text(
                    description
                ),

            "published":
                parse_date(
                    pub_date
                )
        })

    # Atom
    if not records:

        atom_ns = {
            "atom":
                "http://www.w3.org/2005/Atom"
        }

        for entry in root.findall(
            "atom:entry",
            atom_ns
        ):

            title_node = entry.find(
                "atom:title",
                atom_ns
            )

            link_node = entry.find(
                "atom:link",
                atom_ns
            )

            summary_node = entry.find(
                "atom:summary",
                atom_ns
            )

            published_node = entry.find(
                "atom:published",
                atom_ns
            )

            updated_node = entry.find(
                "atom:updated",
                atom_ns
            )

            title = (
                title_node.text
                if title_node is not None
                else ""
            )

            link = (
                link_node.attrib.get(
                    "href"
                )
                if link_node is not None
                else ""
            )

            description = (
                summary_node.text
                if summary_node is not None
                else ""
            )

            date_value = (
                published_node.text
                if published_node is not None
                else (
                    updated_node.text
                    if updated_node is not None
                    else ""
                )
            )

            records.append({

                "title":
                    clean_text(title),

                "url":
                    link.strip(),

                "description":
                    clean_text(
                        description
                    ),

                "published":
                    parse_date(
                        date_value
                    )
            })

    return records


# ==================================================
# SCRAPE ONE SOURCE
# ==================================================

async def scrape_source(
    session,
    source_name,
    feed_url
):

    print(
        f"\nFetching: {source_name}"
    )

    try:

        async with session.get(
            feed_url,
            timeout=aiohttp.ClientTimeout(
                total=30
            )
        ) as response:

            print(
                "HTTP:",
                response.status
            )

            if response.status != 200:

                print(
                    "Source unavailable."
                )

                return []

            xml_data = await response.text(
                errors="ignore"
            )

    except Exception as e:

        print(
            "Fetch error:",
            e
        )

        return []

    articles = parse_rss(
        xml_data
    )

    print(
        "RSS articles:",
        len(articles)
    )

    fresh = []

    for article in articles:

        published = article.get(
            "published"
        )

        # Strict freshness
        if not is_fresh(
            published
        ):

            continue

        title = article.get(
            "title",
            ""
        ).strip()

        url = article.get(
            "url",
            ""
        ).strip()

        if not title or not url:
            continue

        # Full article text
        full_text = await fetch_article_text(
            session,
            url
        )

        if not full_text:

            full_text = article.get(
                "description",
                ""
            )

        fresh.append({

            "schemaVersion":
                "1.0",

            "recordType":
                "NEWS",

            "source_name":
                source_name,

            "source_url":
                url,

            "title":
                title,

            "publishedAt":
                published.isoformat(),

            "content":
                full_text,

            "collectedAt":
                datetime.now(
                    timezone.utc
                ).isoformat()
        })

    print(
        "Fresh 24h articles:",
        len(fresh)
    )

    return fresh


# ==================================================
# MAIN
# ==================================================

async def main():

    print(
        "======================================"
    )

    print(
        "Starting AI News Scraper..."
    )

    print(
        "Target: 5 AI news sources"
    )

    print(
        "Freshness: Last 24 hours only"
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

        tasks = []

        for source_name, feed_url in NEWS_SOURCES.items():

            tasks.append(
                scrape_source(
                    session,
                    source_name,
                    feed_url
                )
            )

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

    all_news = []

    for result in results:

        if isinstance(
            result,
            list
        ):

            all_news.extend(
                result
            )

    # ==================================================
    # DEDUPLICATION
    # ==================================================

    unique = {}

    for article in all_news:

        url = article.get(
            "source_url"
        )

        if url:

            unique[url] = article

    news = list(
        unique.values()
    )

    # ==================================================
    # SAVE CSV
    # ==================================================

    fields = [
        "schemaVersion",
        "recordType",
        "source_name",
        "source_url",
        "title",
        "publishedAt",
        "content",
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
            news
        )

    # ==================================================
    # SAVE JSON
    # ==================================================

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            news,
            file,
            indent=2,
            ensure_ascii=False
        )

    # ==================================================
    # FINAL OUTPUT
    # ==================================================

    print()
    print(
        "======================================"
    )

    print(
        "NEWS SCRAPER COMPLETED"
    )

    print(
        "Fresh unique news:",
        len(news)
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