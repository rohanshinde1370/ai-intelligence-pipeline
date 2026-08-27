import aiohttp
import asyncio
import ssl
import certifi


async def search_github():

    # User कडून paper title घेणे
    query = input("Enter research paper title: ")

    url = "https://api.github.com/search/repositories"

    params = {
        "q": query,
        "per_page": 5
    }

    ssl_context = ssl.create_default_context(
        cafile=certifi.where()
    )

    connector = aiohttp.TCPConnector(
        ssl=ssl_context
    )

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        async with session.get(
            url,
            params=params,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "AI-Intelligence-Pipeline"
            }
        ) as response:

            print("Status:", response.status)

            if response.status != 200:
                print("GitHub API request failed")
                return

            data = await response.json()

            repositories = data.get(
                "items",
                []
            )

            if not repositories:
                print("No GitHub repositories found.")
                return

            print("\n--- GITHUB RESULTS ---")

            for i, repo in enumerate(
                repositories,
                start=1
            ):

                print(f"\n{i}. Repository:", repo["full_name"])

                print(
                    "URL:",
                    repo["html_url"]
                )

                print(
                    "Stars:",
                    repo["stargazers_count"]
                )


asyncio.run(search_github())