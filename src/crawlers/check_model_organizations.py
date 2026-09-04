import csv
from collections import Counter

INPUT_FILE = "data/models_enriched.csv"


def main():

    organizations = Counter()

    with open(
        INPUT_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            organization = row.get(
                "organization",
                ""
            ).strip()

            if organization:
                organizations[organization] += 1

    print("=" * 60)
    print("MODEL ORGANIZATION ANALYSIS")
    print("=" * 60)

    print(f"Total unique organizations: {len(organizations)}")
    print()

    print("Top 30 organizations:")
    print("-" * 60)

    for organization, count in organizations.most_common(30):

        print(
            f"{organization:<35} {count} models"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()