import aiohttp
import asyncio
import ssl
import certifi
from bs4 import BeautifulSoup


async def scrape_arxiv():
    url = "https://arxiv.org/list/cs.AI/recent"

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as response:

            print("Status:", response.status)

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            papers = soup.select("dl#articles dt")

            print("Papers found:", len(papers))
            print("\n--- FIRST 5 PAPERS ---\n")

            for i, dt in enumerate(papers[:5], start=1):

                # Paper URL
                link = dt.find("a", title="Abstract")
                paper_url = "https://arxiv.org" + link["href"]

                # Get corresponding DD element
                dd = dt.find_next_sibling("dd")

                # Title
                title_tag = dd.find("div", class_="list-title")
                title = title_tag.get_text(" ", strip=True)
                title = title.replace("Title:", "").strip()

                # Authors
                authors_tag = dd.find("div", class_="list-authors")
                authors = [
                    a.get_text(strip=True)
                    for a in authors_tag.find_all("a")
                ]

                # Print
                print(f"{i}. {title}")
                print("Authors:", ", ".join(authors))
                print("URL:", paper_url)
                print("-" * 80)


asyncio.run(scrape_arxiv())