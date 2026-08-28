import csv
import re
from pathlib import Path
from datetime import datetime, timezone


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

STARTUPS_FILE = BASE_DIR / "startups.csv"
PRODUCTS_FILE = BASE_DIR / "products.csv"
RESEARCH_FILE = BASE_DIR / "research_papers.csv"
JOBS_FILE = BASE_DIR / "jobs.csv"
NEWS_FILE = BASE_DIR / "news.csv"

OUTPUT_FILE = BASE_DIR / "entity_relationships.csv"


# ==================================================
# LOAD CSV
# ==================================================

def load_csv(path):

    with open(
        path,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        return list(
            csv.DictReader(file)
        )


# ==================================================
# NORMALIZE TEXT
# ==================================================

def normalize(value):

    if not value:
        return ""

    value = str(value).lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return " ".join(
        value.split()
    ).strip()


# ==================================================
# ENTITY ID
# ==================================================

def make_entity_id(index):

    return f"STARTUP-{index:04d}"


# ==================================================
# BUILD CANONICAL STARTUP ENTITIES
# ==================================================

def build_startup_entities(startups):

    entities = []

    for index, startup in enumerate(
        startups,
        start=1
    ):

        name = startup.get(
            "entityName",
            ""
        ).strip()

        if not name:
            continue

        entity = {

            "entityId":
                make_entity_id(index),

            "entityName":
                name,

            "normalizedName":
                normalize(name),

            "entityType":
                "STARTUP",

            "startupUrl":
                startup.get(
                    "source_url",
                    ""
                )
        }

        entities.append(entity)

    return entities


# ==================================================
# ADD RELATIONSHIP
# ==================================================

def add_relationship(
    relationships,
    entity,
    record_type,
    relationship_type,
    source_url,
    confidence
):

    relationships.append({

        "entityId":
            entity["entityId"],

        "entityName":
            entity["entityName"],

        "entityType":
            entity["entityType"],

        "recordType":
            record_type,

        "relationshipType":
            relationship_type,

        "source_url":
            source_url,

        "confidence":
            confidence,

        "mappedAt":
            datetime.now(
                timezone.utc
            ).isoformat()
    })


# ==================================================
# PRODUCT MAPPING
# ==================================================

def map_products(
    products,
    entities,
    relationships
):

    entity_lookup = {

        entity["normalizedName"]:
            entity

        for entity in entities

    }

    mapped = 0

    for product in products:

        startup_name = normalize(
            product.get(
                "startupName",
                ""
            )
        )

        if not startup_name:
            continue

        entity = entity_lookup.get(
            startup_name
        )

        if entity:

            add_relationship(

                relationships,

                entity,

                "PRODUCT",

                "HAS_PRODUCT",

                product.get(
                    "source_url",
                    ""
                ),

                1.0
            )

            mapped += 1

    return mapped


# ==================================================
# JOB MAPPING
# ==================================================

def map_jobs(
    jobs,
    entities,
    relationships
):

    entity_lookup = {

        entity["normalizedName"]:
            entity

        for entity in entities

    }

    mapped = 0

    for job in jobs:

        company = normalize(
            job.get(
                "company",
                ""
            )
        )

        if not company:
            continue

        entity = entity_lookup.get(
            company
        )

        if entity:

            add_relationship(

                relationships,

                entity,

                "JOB",

                "HAS_JOB",

                job.get(
                    "source_url",
                    ""
                ),

                1.0
            )

            mapped += 1

    return mapped


# ==================================================
# TEXT MAPPING
# ==================================================

def map_text_records(
    records,
    record_type,
    entities,
    relationships
):

    mapped = 0

    # Longer company names first
    entities_sorted = sorted(

        entities,

        key=lambda entity:
            len(
                entity["normalizedName"]
            ),

        reverse=True
    )

    for record in records:

        # ------------------------------------------
        # RESEARCH PAPER
        # ------------------------------------------

        if record_type == "RESEARCH_PAPER":

            text = " ".join([

                record.get(
                    "title",
                    ""
                ),

                record.get(
                    "authors",
                    ""
                )

            ])

        # ------------------------------------------
        # NEWS
        # ------------------------------------------

        else:

            text = " ".join([

                record.get(
                    "title",
                    ""
                ),

                record.get(
                    "content",
                    ""
                )

            ])

        normalized_text = normalize(
            text
        )

        if not normalized_text:
            continue

        for entity in entities_sorted:

            company_name = entity[
                "normalizedName"
            ]

            if not company_name:
                continue

            words = company_name.split()

            # Ignore very short one-word names
            if (
                len(words) == 1
                and len(company_name) < 5
            ):
                continue

            pattern = (
                r"\b"
                + re.escape(company_name)
                + r"\b"
            )

            if re.search(
                pattern,
                normalized_text
            ):

                if record_type == "RESEARCH_PAPER":

                    relationship_type = (
                        "MENTIONED_IN_RESEARCH"
                    )

                else:

                    relationship_type = (
                        "MENTIONED_IN_NEWS"
                    )

                source_url = record.get(
                    "source_url",
                    ""
                )

                if not source_url:

                    source_url = record.get(
                        "paper_url",
                        ""
                    )

                add_relationship(

                    relationships,

                    entity,

                    record_type,

                    relationship_type,

                    source_url,

                    0.85
                )

                mapped += 1

                # One startup per record
                break

    return mapped


# ==================================================
# REMOVE DUPLICATES
# ==================================================

def deduplicate_relationships(
    relationships
):

    unique = {}

    for relationship in relationships:

        key = (

            relationship["entityId"],

            relationship["recordType"],

            relationship["source_url"]

        )

        unique[key] = relationship

    return list(
        unique.values()
    )


# ==================================================
# SAVE CSV
# ==================================================

def save_relationships(
    relationships
):

    fields = [

        "entityId",
        "entityName",
        "entityType",
        "recordType",
        "relationshipType",
        "source_url",
        "confidence",
        "mappedAt"

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
            relationships
        )


# ==================================================
# MAIN
# ==================================================

def main():

    print(
        "======================================"
    )

    print(
        "Starting Entity Mapping..."
    )

    print(
        "======================================"
    )

    # ------------------------------------------
    # LOAD DATA
    # ------------------------------------------

    startups = load_csv(
        STARTUPS_FILE
    )

    products = load_csv(
        PRODUCTS_FILE
    )

    research = load_csv(
        RESEARCH_FILE
    )

    jobs = load_csv(
        JOBS_FILE
    )

    news = load_csv(
        NEWS_FILE
    )

    print(
        "Startups:",
        len(startups)
    )

    print(
        "Products:",
        len(products)
    )

    print(
        "Research:",
        len(research)
    )

    print(
        "Jobs:",
        len(jobs)
    )

    print(
        "News:",
        len(news)
    )

    # ------------------------------------------
    # CANONICAL ENTITIES
    # ------------------------------------------

    entities = build_startup_entities(
        startups
    )

    print(
        "Canonical entities:",
        len(entities)
    )

    relationships = []

    # ------------------------------------------
    # PRODUCTS
    # ------------------------------------------

    product_count = map_products(

        products,

        entities,

        relationships
    )

    print(
        "Product relationships:",
        product_count
    )

    # ------------------------------------------
    # JOBS
    # ------------------------------------------

    job_count = map_jobs(

        jobs,

        entities,

        relationships
    )

    print(
        "Job relationships:",
        job_count
    )

    # ------------------------------------------
    # RESEARCH
    # ------------------------------------------

    research_count = map_text_records(

        research,

        "RESEARCH_PAPER",

        entities,

        relationships
    )

    print(
        "Research relationships:",
        research_count
    )

    # ------------------------------------------
    # NEWS
    # ------------------------------------------

    news_count = map_text_records(

        news,

        "NEWS",

        entities,

        relationships
    )

    print(
        "News relationships:",
        news_count
    )

    # ------------------------------------------
    # DEDUPLICATION
    # ------------------------------------------

    relationships = (
        deduplicate_relationships(
            relationships
        )
    )

    # ------------------------------------------
    # SAVE
    # ------------------------------------------

    save_relationships(
        relationships
    )

    # ------------------------------------------
    # FINAL OUTPUT
    # ------------------------------------------

    print()

    print(
        "======================================"
    )

    print(
        "ENTITY MAPPING COMPLETED"
    )

    print(
        "Unique relationships:",
        len(relationships)
    )

    print(
        "Output:",
        OUTPUT_FILE
    )

    print(
        "======================================"
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()