import csv
from pathlib import Path


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

FILES = {
    "STARTUPS": BASE_DIR / "startups.csv",
    "PRODUCTS": BASE_DIR / "products.csv",
    "RESEARCH": BASE_DIR / "research_papers.csv",
    "NEWS": BASE_DIR / "news.csv",
    "JOBS": BASE_DIR / "jobs.csv",

    # Models file is inside data folder
    "MODELS": BASE_DIR / "data" / "models_enriched.csv",

    "RELATIONSHIPS": BASE_DIR / "entity_relationships.csv",
}


# ==================================================
# LOAD CSV
# ==================================================

def load_csv(path):

    if not path.exists():
        print(f"File not found: {path}")
        return []

    with open(
        path,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        return list(csv.DictReader(file))


# ==================================================
# CHECK MISSING VALUES
# ==================================================

def check_missing(records, required_fields):

    missing_count = 0

    for record in records:

        for field in required_fields:

            value = record.get(field, "")

            if not value or not value.strip():
                missing_count += 1

    return missing_count


# ==================================================
# CHECK DUPLICATES
# ==================================================

def check_duplicates(records, field):

    seen = set()
    duplicates = 0

    for record in records:

        value = record.get(field, "").strip().lower()

        if not value:
            continue

        if value in seen:
            duplicates += 1
        else:
            seen.add(value)

    return duplicates


# ==================================================
# DATA QUALITY CHECK
# ==================================================

def analyze_file(name, path, required_fields, unique_field):

    records = load_csv(path)

    print()
    print("--------------------------------------")
    print(name)
    print("--------------------------------------")

    print("Rows:", len(records))

    if not records:
        return

    missing = check_missing(
        records,
        required_fields
    )

    duplicates = check_duplicates(
        records,
        unique_field
    )

    print(
        "Missing required values:",
        missing
    )

    print(
        f"Duplicate {unique_field}:",
        duplicates
    )

    if missing == 0:
        print("Required fields: PASS")
    else:
        print("Required fields: CHECK")

    if duplicates == 0:
        print("Duplicates: PASS")
    else:
        print("Duplicates: CHECK")


# ==================================================
# RELATIONSHIP CHECK
# ==================================================

def analyze_relationships():

    records = load_csv(
        FILES["RELATIONSHIPS"]
    )

    print()
    print("--------------------------------------")
    print("ENTITY RELATIONSHIPS")
    print("--------------------------------------")

    print(
        "Total relationships:",
        len(records)
    )

    if not records:
        return

    relationship_types = {}

    for record in records:

        relationship = record.get(
            "relationshipType",
            ""
        ).strip()

        if relationship:

            relationship_types[
                relationship
            ] = relationship_types.get(
                relationship,
                0
            ) + 1

    print()
    print("Relationship counts:")

    for relationship, count in sorted(
        relationship_types.items()
    ):

        print(
            f"{relationship}: {count}"
        )

    invalid_confidence = 0

    for record in records:

        try:

            confidence = float(
                record.get(
                    "confidence",
                    ""
                )
            )

            if confidence < 0 or confidence > 1:
                invalid_confidence += 1

        except (ValueError, TypeError):

            invalid_confidence += 1

    print()
    print(
        "Invalid confidence values:",
        invalid_confidence
    )

    if invalid_confidence == 0:
        print("Confidence check: PASS")
    else:
        print("Confidence check: CHECK")


# ==================================================
# MAIN
# ==================================================

def main():

    print("======================================")
    print("Starting Data Quality Check...")
    print("======================================")

    # ------------------------------------------------
    # STARTUPS
    # ------------------------------------------------

    analyze_file(
        "STARTUPS",
        FILES["STARTUPS"],
        [
            "entityName",
            "source_url"
        ],
        "entityName"
    )

    # ------------------------------------------------
    # PRODUCTS
    # ------------------------------------------------

    analyze_file(
        "PRODUCTS",
        FILES["PRODUCTS"],
        [
            "productName",
            "startupName",
            "source_url"
        ],
        "productName"
    )

    # ------------------------------------------------
    # RESEARCH PAPERS
    # ------------------------------------------------

    analyze_file(
        "RESEARCH PAPERS",
        FILES["RESEARCH"],
        [
            "title",
            "source_url"
        ],
        "paper_url"
    )

    # ------------------------------------------------
    # NEWS
    # ------------------------------------------------

    analyze_file(
        "NEWS",
        FILES["NEWS"],
        [
            "title",
            "source_url"
        ],
        "source_url"
    )

    # ------------------------------------------------
    # JOBS
    # ------------------------------------------------

    analyze_file(
        "JOBS",
        FILES["JOBS"],
        [
            "company",
            "title",
            "source_url"
        ],
        "source_url"
    )

    # ------------------------------------------------
    # MODELS
    # ------------------------------------------------

    analyze_file(
        "MODELS",
        FILES["MODELS"],
        [
            "model_name",
            "organization",
            "source_url",
            "official_website",
            "logo_url",
            "description"
        ],
        "source_url"
    )

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------

    analyze_relationships()

    print()
    print("======================================")
    print("DATA QUALITY CHECK COMPLETED")
    print("======================================")


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    main()