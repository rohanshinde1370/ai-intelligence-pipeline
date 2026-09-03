
import csv
import os
import requests
import time

INPUT_FILE = "data/models.csv"
OUTPUT_FILE = "data/models_enriched.csv"

HF_API_URL = "https://huggingface.co"
REQUEST_TIMEOUT = 30
SLEEP_SECONDS = 0.2


def clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def fetch_readme(model_id):
    url = f"{HF_API_URL}/{model_id}/raw/main/README.md"

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 200:
            return response.text

    except requests.RequestException:
        pass

    return ""


def extract_description(readme):
    if not readme:
        return ""

    lines = readme.splitlines()
    description_lines = []

    for line in lines:

        line = line.strip()

        if not line:
            if description_lines:
                break
            continue

        # Ignore YAML front matter
        if line.startswith("---"):
            continue

        # Ignore headings
        if line.startswith("#"):
            if description_lines:
                break
            continue

        # Ignore badges
        if line.startswith("[!["):
            continue

        description_lines.append(line)

        if len(" ".join(description_lines)) >= 500:
            break

    description = " ".join(description_lines)

    return clean_text(description)[:500]


def create_fallback_description(record):
    """
    Creates a conservative description using only
    verified metadata already present in the dataset.
    """

    model_name = record["model_name"]
    organization = record["organization"]
    pipeline = record["pipeline_tag"]
    library = record["library_name"]

    description_parts = []

    if organization:
        description_parts.append(
            f"{model_name} is an AI model published by "
            f"{organization}."
        )
    else:
        description_parts.append(
            f"{model_name} is an AI model."
        )

    if pipeline:
        description_parts.append(
            f"It is listed for the {pipeline} task."
        )

    if library:
        description_parts.append(
            f"It is available through the {library} library."
        )

    return clean_text(" ".join(description_parts))


def read_models():

    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return []

    records = []

    with open(
        INPUT_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            model_name = clean_text(
                row.get("model_name")
            )

            organization = clean_text(
                row.get("organization")
            )

            source_url = clean_text(
                row.get("source_url")
            )

            if not model_name or not source_url:
                continue

            records.append({
                "model_name": model_name,
                "organization": organization,
                "source_url": source_url,
                "downloads": clean_text(
                    row.get("downloads")
                ),
                "likes": clean_text(
                    row.get("likes")
                ),
                "pipeline_tag": clean_text(
                    row.get("pipeline_tag")
                ),
                "library_name": clean_text(
                    row.get("library_name")
                ),
                "description": "",
                "official_website": "",
                "logo_url": ""
            })

    return records


def remove_duplicates(records):

    unique_records = []
    seen = set()

    for record in records:

        key = (
            record["organization"].lower(),
            record["model_name"].lower()
        )

        if key in seen:
            continue

        seen.add(key)
        unique_records.append(record)

    return unique_records


def enrich_models(records):

    total = len(records)

    print("=" * 60)
    print("Starting Model Card README Enrichment...")
    print("=" * 60)

    readme_found = 0
    fallback_used = 0

    for index, record in enumerate(
        records,
        start=1
    ):

        model_id = record["source_url"].replace(
            "https://huggingface.co/",
            "",
            1
        )

        print(
            f"[{index}/{total}] "
            f"{record['organization']}/"
            f"{record['model_name']}"
        )

        readme = fetch_readme(model_id)

        description = extract_description(readme)

        if description:

            record["description"] = description
            readme_found += 1

        else:

            # Safe metadata-based fallback
            record["description"] = (
                create_fallback_description(record)
            )

            fallback_used += 1

        time.sleep(SLEEP_SECONDS)

    print("=" * 60)
    print(f"README descriptions found: {readme_found}")
    print(f"Fallback descriptions used: {fallback_used}")
    print("=" * 60)

    return records


def save_models(records):

    os.makedirs("data", exist_ok=True)

    fieldnames = [
        "model_name",
        "organization",
        "source_url",
        "downloads",
        "likes",
        "pipeline_tag",
        "library_name",
        "description",
        "official_website",
        "logo_url"
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


def main():

    print("=" * 60)
    print("Starting Models Enrichment...")
    print("=" * 60)

    records = read_models()

    print(f"Records read: {len(records)}")

    records = remove_duplicates(records)

    print(
        f"Records after duplicate removal: "
        f"{len(records)}"
    )

    records = enrich_models(records)

    save_models(records)

    descriptions = sum(
        1
        for record in records
        if record["description"]
    )

    print("=" * 60)
    print("Enrichment completed!")
    print("=" * 60)

    print(f"Final records: {len(records)}")
    print(f"Descriptions available: {descriptions}")
    print(
        f"Descriptions missing: "
        f"{len(records) - descriptions}"
    )

    print(f"Output: {OUTPUT_FILE}")

    print("=" * 60)


if __name__ == "__main__":
    main()