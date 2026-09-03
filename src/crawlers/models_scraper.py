import requests
import csv
import os


API_URL = "https://huggingface.co/api/models"

OUTPUT_FILE = "data/models.csv"

LIMIT = 2000


def fetch_models(limit=2000):

    params = {
        "limit": limit,
        "sort": "downloads",
        "direction": -1
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    return response.json()


def clean_model(model):

    model_id = model.get("id", "").strip()

    if not model_id:
        return None

    if "/" in model_id:

        organization = model_id.split("/")[0]
        model_name = model_id.split("/")[-1]

    else:

        organization = ""
        model_name = model_id

    return {
        "model_name": model_name,
        "organization": organization,
        "source_url": f"https://huggingface.co/{model_id}",
        "downloads": model.get("downloads", 0),
        "likes": model.get("likes", 0),
        "pipeline_tag": model.get("pipeline_tag", ""),
        "library_name": model.get("library_name", "")
    }


def save_to_csv(records):

    os.makedirs("data", exist_ok=True)

    fieldnames = [
        "model_name",
        "organization",
        "source_url",
        "downloads",
        "likes",
        "pipeline_tag",
        "library_name"
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
    print("Starting Models Extraction...")
    print("=" * 60)

    models = fetch_models(LIMIT)

    print(f"Models received: {len(models)}")

    records = []

    seen = set()

    for model in models:

        record = clean_model(model)

        if record is None:
            continue

        # Unique key using organization + model name
        key = (
            record["organization"].lower(),
            record["model_name"].lower()
        )

        # Remove duplicates
        if key in seen:
            continue

        seen.add(key)

        records.append(record)

    save_to_csv(records)

    print(f"Models saved: {len(records)}")
    print(f"Output: {OUTPUT_FILE}")

    print("=" * 60)
    print("Extraction completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()