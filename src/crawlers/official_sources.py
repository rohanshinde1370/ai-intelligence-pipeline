import csv
import os
import re
import time
import requests
from urllib.parse import quote, urlparse

INPUT_FILE = "data/organization_mapping.csv"
OUTPUT_FILE = "data/organization_sources.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 AI-Intelligence-Pipeline/1.0"
}

# Known official mappings for high-confidence organizations.
KNOWN_SOURCES = {
    "openai": "https://openai.com/",
    "google": "https://www.google.com/",
    "microsoft": "https://www.microsoft.com/",
    "nvidia": "https://www.nvidia.com/",
    "amazon": "https://www.amazon.com/",
    "qwen": "https://qwen.ai/",
    "deepseek-ai": "https://www.deepseek.com/",
    "unsloth": "https://unsloth.ai/",
    "mistralai": "https://mistral.ai/",
    "cohere": "https://cohere.com/",
    "anthropic": "https://www.anthropic.com/",
    "stabilityai": "https://stability.ai/",
    "bytedance": "https://www.bytedance.com/",
    "tencent": "https://www.tencent.com/",
    "apple": "https://www.apple.com/",
    "ibm": "https://www.ibm.com/",
    "intel": "https://www.intel.com/",
    "adobe": "https://www.adobe.com/",
    "salesforce": "https://www.salesforce.com/",
    "huggingface": "https://huggingface.co/",
    "hugging-face": "https://huggingface.co/",
}


def clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalize_name(name):
    name = clean_text(name).lower()
    name = name.replace("_", "-")
    name = re.sub(r"\s+", "-", name)
    return name.strip("-")


def check_website(url):
    """
    Verify that the URL is reachable.
    """
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
            allow_redirects=True
        )

        if response.status_code < 400:
            return response.url

    except requests.RequestException:
        pass

    return ""


def find_official_website(organization):
    """
    Search DuckDuckGo for the organization's official website.
    Only accept results whose domain is not Hugging Face,
    GitHub, Wikipedia, LinkedIn, etc.
    """

    query = quote(
        f"{organization} official website"
    )

    search_url = (
        f"https://html.duckduckgo.com/html/?q={query}"
    )

    try:
        response = requests.get(
            search_url,
            headers=HEADERS,
            timeout=15
        )

        if response.status_code != 200:
            return "", ""

        html = response.text

        links = re.findall(
            r'class="result__a"[^>]+href="([^"]+)"',
            html
        )

        blocked_domains = [
            "huggingface.co",
            "github.com",
            "wikipedia.org",
            "linkedin.com",
            "twitter.com",
            "x.com",
            "facebook.com",
            "reddit.com",
            "youtube.com"
        ]

        for link in links:

            if link.startswith("//"):
                link = "https:" + link

            parsed = urlparse(link)

            domain = parsed.netloc.lower()

            if not domain:
                continue

            if any(
                blocked in domain
                for blocked in blocked_domains
            ):
                continue

            clean_url = (
                f"{parsed.scheme}://{parsed.netloc}/"
            )

            verified_url = check_website(clean_url)

            if verified_url:
                return verified_url, "DuckDuckGo search + HTTP verification"

    except Exception as e:
        print(f"Search error for {organization}: {e}")

    return "", ""


def get_logo_url(website):
    """
    Use the official website favicon as the logo URL.
    This is only populated after the official website
    itself has been verified.
    """

    if not website:
        return ""

    parsed = urlparse(website)

    if not parsed.netloc:
        return ""

    return (
        f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
    )


def main():

    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    records = []

    with open(
        INPUT_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for index, row in enumerate(reader, start=1):

            organization = clean_text(
                row.get("organization")
            )

            model_count = clean_text(
                row.get("model_count")
            )

            if not organization:
                continue

            key = normalize_name(organization)

            print(
                f"[{index}] Processing: {organization}"
            )

            website = ""
            source = ""

            # 1. Known high-confidence mapping
            if key in KNOWN_SOURCES:

                candidate = KNOWN_SOURCES[key]

                verified = check_website(candidate)

                if verified:
                    website = verified
                    source = "Known official domain + HTTP verification"

            # 2. Search if not found
            if not website:

                website, source = find_official_website(
                    organization
                )

            # 3. Logo only after website verification
            logo_url = get_logo_url(website)

            website_verified = (
                "YES" if website else "NO"
            )

            logo_verified = (
                "YES" if logo_url else "NO"
            )

            records.append({
                "organization": organization,
                "model_count": model_count,
                "official_website": website,
                "logo_url": logo_url,
                "website_verified": website_verified,
                "logo_verified": logo_verified,
                "verification_source": source
            })

            time.sleep(1)

    os.makedirs("data", exist_ok=True)

    fieldnames = [
        "organization",
        "model_count",
        "official_website",
        "logo_url",
        "website_verified",
        "logo_verified",
        "verification_source"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(records)

    verified_websites = sum(
        r["website_verified"] == "YES"
        for r in records
    )

    verified_logos = sum(
        r["logo_verified"] == "YES"
        for r in records
    )

    print("=" * 60)
    print("OFFICIAL SOURCE VERIFICATION COMPLETED")
    print("=" * 60)
    print(f"Organizations: {len(records)}")
    print(f"Verified websites: {verified_websites}")
    print(f"Verified logos: {verified_logos}")
    print(
        f"Unverified organizations: "
        f"{len(records) - verified_websites}"
    )
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()