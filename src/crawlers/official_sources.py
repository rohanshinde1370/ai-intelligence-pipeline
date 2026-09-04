import csv
import os
from urllib.parse import urlparse

INPUT_FILE = "data/models_final.csv"
OUTPUT_FILE = "data/organization_sources.csv"

# ============================================================
# VERIFIED OFFICIAL SOURCES
# ============================================================

KNOWN_SOURCES = {
    "openai": "https://openai.com/",
    "google": "https://www.google.com/",
    "microsoft": "https://www.microsoft.com/",
    "nvidia": "https://www.nvidia.com/",
    "amazon": "https://www.amazon.com/",
    "apple": "https://www.apple.com/",
    "ibm": "https://www.ibm.com/",
    "intel": "https://www.intel.com/",
    "amd": "https://www.amd.com/",
    "qualcomm": "https://www.qualcomm.com/",
    "oracle": "https://www.oracle.com/",
    "adobe": "https://www.adobe.com/",
    "salesforce": "https://www.salesforce.com/",
    "databricks": "https://www.databricks.com/",
    "samsung": "https://www.samsung.com/",
    "sony": "https://www.sony.com/",
    "anthropic": "https://www.anthropic.com/",
    "deepseek-ai": "https://www.deepseek.com/",
    "mistralai": "https://mistral.ai/",
    "cohere": "https://cohere.com/",
    "stabilityai": "https://stability.ai/",
    "stability-ai": "https://stability.ai/",
    "bytedance": "https://www.bytedance.com/",
    "tencent": "https://www.tencent.com/",
    "alibaba": "https://www.alibabagroup.com/",
    "baidu": "https://www.baidu.com/",
    "01-ai": "https://01.ai/",
    "zhipuai": "https://www.zhipu.ai/",
    "tiiuae": "https://www.tii.ae/",
    "ai21labs": "https://www.ai21.com/",
    "ai21": "https://www.ai21.com/",
    "reka-ai": "https://www.reka.ai/",
    "writer": "https://writer.com/",
    "perplexity-ai": "https://www.perplexity.ai/",
    "xai": "https://x.ai/",
    "xai-org": "https://x.ai/",
    "black-forest-labs": "https://blackforestlabs.ai/",
    "runwayml": "https://runwayml.com/",
    "lightricks": "https://www.lightricks.com/",
    "nomic-ai": "https://www.nomic.ai/",
    "voyageai": "https://www.voyageai.com/",
    "togethercomputer": "https://www.together.ai/",
    "together-ai": "https://www.together.ai/",
    "groq": "https://groq.com/",
    "cerebras": "https://www.cerebras.ai/",

    # Meta / Facebook
    "facebook": "https://about.meta.com/",
    "facebookresearch": "https://ai.meta.com/",
    "meta": "https://about.meta.com/",
    "meta-llama": "https://www.llama.com/",

    # Google research / models
    "google-research": "https://research.google/",
    "google-bert": "https://research.google/",
    "google-t5": "https://research.google/",
    "google-research-bert": "https://research.google/",
    "gemma": "https://ai.google.dev/gemma",
    "deepmind": "https://deepmind.google/",

    # Microsoft research / models
    "microsoftresearch": "https://www.microsoft.com/en-us/research/",
    "microsoft-phi": "https://azure.microsoft.com/en-us/products/phi",

    # AI / research organizations
    "allenai": "https://allenai.org/",
    "eleutherai": "https://www.eleuther.ai/",
    "stanford": "https://www.stanford.edu/",
    "stanfordaimi": "https://aimi.stanford.edu/",
    "mosaicml": "https://www.databricks.com/",

    # Hugging Face
    "huggingface": "https://huggingface.co/",
    "hugging-face": "https://huggingface.co/",

    # Known model organizations
    "qwen": "https://qwen.ai/",
    "unsloth": "https://unsloth.ai/",
}


# ============================================================
# BAD / THIRD-PARTY DOMAINS
# ============================================================

BLOCKED_DOMAINS = {
    "duckduckgo.com",
    "google.com",
    "bing.com",
    "yahoo.com",
    "wikipedia.org",
    "github.com",
    "gitlab.com",
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "youtube.com",
    "medium.com",
    "pypi.org",
    "npmjs.com",
}


def normalize_org(value):
    """Normalize organization name for matching."""
    if not value:
        return ""

    value = value.strip().lower()

    replacements = {
        "facebook ai": "facebookresearch",
        "facebookai": "facebookresearch",
        "meta ai": "meta",
        "google ai": "google-research",
        "google research": "google-research",
        "microsoft research": "microsoftresearch",
        "hugging face": "huggingface",
    }

    return replacements.get(value, value)


def get_domain(url):
    """Extract clean domain."""
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        domain = domain.replace("www.", "")
        return domain
    except Exception:
        return ""


def is_valid_official_url(url):
    """Reject search engines and obvious third-party sites."""
    if not url:
        return False

    domain = get_domain(url)

    if not domain:
        return False

    for blocked in BLOCKED_DOMAINS:
        if domain == blocked or domain.endswith("." + blocked):
            return False

    return url.startswith("http://") or url.startswith("https://")


def logo_url(website):
    """
    Use official website favicon.
    This avoids additional network calls.
    """
    if not website:
        return ""

    domain = get_domain(website)

    if not domain:
        return ""

    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"


def read_models():
    """Read model data and collect unique organizations."""
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    organizations = {}

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            org = row.get("organization", "").strip()

            if not org:
                continue

            key = normalize_org(org)

            if key not in organizations:
                organizations[key] = {
                    "organization": org,
                    "model_url": row.get("source_url", "").strip()
                }

    return organizations


def process_organizations():
    organizations = read_models()

    results = []

    for key, info in organizations.items():

        organization = info["organization"]
        model_url = info["model_url"]

        # ----------------------------------------------------
        # 1. Known official organization
        # ----------------------------------------------------

        if key in KNOWN_SOURCES:

            website = KNOWN_SOURCES[key]

            if is_valid_official_url(website):

                results.append({
                    "organization": organization,
                    "official_website": website,
                    "logo_url": logo_url(website),
                    "verification_status": "verified_official",
                    "source_type": "known_official_mapping"
                })

                continue

        # ----------------------------------------------------
        # 2. Safe fallback
        #
        # Do NOT guess an organization website.
        # Use the model's primary Hugging Face page.
        # ----------------------------------------------------

        if model_url and "huggingface.co/" in model_url:

            results.append({
                "organization": organization,
                "official_website": model_url,
                "logo_url": "https://huggingface.co/front/assets/huggingface_logo-noborder.svg",
                "verification_status": "primary_model_source",
                "source_type": "Hugging Face model page"
            })

        else:

            results.append({
                "organization": organization,
                "official_website": "",
                "logo_url": "",
                "verification_status": "unverified",
                "source_type": ""
            })

    return results


def save_results(results):

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    fieldnames = [
        "organization",
        "official_website",
        "logo_url",
        "verification_status",
        "source_type"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)


def main():

    print("=" * 60)
    print("FAST OFFICIAL SOURCE VERIFICATION")
    print("=" * 60)

    results = process_organizations()

    save_results(results)

    verified = sum(
        1
        for r in results
        if r["verification_status"] == "verified_official"
    )

    primary = sum(
        1
        for r in results
        if r["verification_status"] == "primary_model_source"
    )

    unverified = sum(
        1
        for r in results
        if r["verification_status"] == "unverified"
    )

    print(f"Organizations: {len(results)}")
    print(f"Verified official websites: {verified}")
    print(f"Primary model sources: {primary}")
    print(f"Unverified: {unverified}")
    print(f"Output: {OUTPUT_FILE}")

    print("=" * 60)
    print("COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()