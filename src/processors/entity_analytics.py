import csv
from pathlib import Path
from collections import defaultdict


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "entity_relationships.csv"

OUTPUT_FILE = BASE_DIR / "entity_analytics.csv"


# ==================================================
# LOAD CSV
# ==================================================

def load_relationships():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        return list(
            csv.DictReader(file)
        )


# ==================================================
# BUILD ANALYTICS
# ==================================================

def build_analytics(relationships):

    analytics = defaultdict(
        lambda: {
            "entityName": "",
            "HAS_PRODUCT": 0,
            "HAS_JOB": 0,
            "MENTIONED_IN_RESEARCH": 0,
            "MENTIONED_IN_NEWS": 0
        }
    )

    for relationship in relationships:

        entity_id = relationship.get(
            "entityId",
            ""
        ).strip()

        entity_name = relationship.get(
            "entityName",
            ""
        ).strip()

        relationship_type = relationship.get(
            "relationshipType",
            ""
        ).strip()

        if not entity_id:
            continue

        analytics[entity_id]["entityName"] = entity_name

        if relationship_type in analytics[entity_id]:

            analytics[entity_id][
                relationship_type
            ] += 1

    results = []

    for entity_id, data in analytics.items():

        total_relationships = (
            data["HAS_PRODUCT"]
            + data["HAS_JOB"]
            + data["MENTIONED_IN_RESEARCH"]
            + data["MENTIONED_IN_NEWS"]
        )

        results.append({

            "entityId":
                entity_id,

            "entityName":
                data["entityName"],

            "productCount":
                data["HAS_PRODUCT"],

            "jobCount":
                data["HAS_JOB"],

            "researchMentionCount":
                data["MENTIONED_IN_RESEARCH"],

            "newsMentionCount":
                data["MENTIONED_IN_NEWS"],

            "totalRelationships":
                total_relationships
        })

    return results


# ==================================================
# SAVE CSV
# ==================================================

def save_analytics(results):

    fields = [
        "entityId",
        "entityName",
        "productCount",
        "jobCount",
        "researchMentionCount",
        "newsMentionCount",
        "totalRelationships"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        writer.writerows(
            results
        )


# ==================================================
# MAIN
# ==================================================

def main():

    print(
        "======================================"
    )

    print(
        "Starting Entity Analytics..."
    )

    print(
        "======================================"
    )

    relationships = load_relationships()

    print(
        "Input relationships:",
        len(relationships)
    )

    analytics = build_analytics(
        relationships
    )

    print(
        "Entities analyzed:",
        len(analytics)
    )

    save_analytics(
        analytics
    )

    print()
    print(
        "======================================"
    )

    print(
        "ENTITY ANALYTICS COMPLETED"
    )

    print(
        "Output:",
        OUTPUT_FILE
    )

    print(
        "======================================"
    )


if __name__ == "__main__":
    main()