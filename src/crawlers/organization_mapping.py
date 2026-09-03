import csv
import os

INPUT_FILE = "data/models_enriched.csv"
OUTPUT_FILE = "data/organization_mapping.csv"


def clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def main():

    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    organizations = {}

    with open(
        INPUT_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            organization = clean_text(
                row.get("organization")
            )

            if not organization:
                continue

            key = organization.lower()

            if key not in organizations:

                organizations[key] = {
                    "organization": organization,
                    "model_count": 0,
                    "official_website": "",
                    "logo_url": ""
                }

            organizations[key]["model_count"] += 1

    os.makedirs("data", exist_ok=True)

    fieldnames = [
        "organization",
        "model_count",
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

        for record in sorted(
            organizations.values(),
            key=lambda x: x["model_count"],
            reverse=True
        ):
            writer.writerow(record)

    print("=" * 60)
    print("ORGANIZATION MAPPING COMPLETED")
    print("=" * 60)

    print(
        f"Unique organizations: "
        f"{len(organizations)}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()