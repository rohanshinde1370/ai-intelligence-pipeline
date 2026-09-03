import csv
import os
import requests
import time


# ============================================================
# FILE CONFIGURATION
# ============================================================

INPUT_FILE = "data/models.csv"
OUTPUT_FILE = "data/models_enriched.csv"

API_URL = "https://huggingface.co/api/models"


# ============================================================
# GET MODEL INFO
# ============================================================

def get_model_info(model_url):
    """
    Fetch detailed information from the official
    Hugging Face model API.
    """

    try:
        response = requests.get(
            model_url,
            timeout=30
        )

        if response.status_code != 200:
            return {}

        return response.json()

    except Exception as e:
        print(f"Error fetching model info: {e}")
        return {}


# ============================================================
# GET MODEL DESCRIPTION
# ============================================================

def get_description(model_id):
    """
    Get model description from the official
    Hugging Face model card.
    """

    url = f"https://huggingface.co/{model_id}/raw/main/README.md"

    try:
        response = requests.get(
            url,
            timeout=30
        )

        if response.status_code != 200:
            return ""

        text = response.text.strip()

        # ----------------------------------------------------
        # Remove YAML frontmatter
        # ----------------------------------------------------

        if text.startswith("---"):

            parts = text.split("---", 2)

            if len(parts) >= 3:
                text = parts[2].strip()

        # ----------------------------------------------------
        # Extract first meaningful paragraph
        # ----------------------------------------------------

        lines = text.splitlines()

        description = []

        for line in lines:

            line = line.strip()

            # Ignore empty lines
            if not line:

                if description:
                    break

                continue

            # Ignore markdown headings
            if line.startswith("#"):
                continue

            # Ignore common markdown image lines
            if line.startswith("!["):
                continue

            description.append(line)

            # Limit description size
            if len(" ".join(description)) >= 500:
                break

        result = " ".join(description).strip()

        return result[:500]

    except Exception as e:

        print(f"Description error for {model_id}: {e}")

        return ""


# ============================================================
# FALLBACK DESCRIPTION
# ============================================================

def create_fallback_description(model_name, organization):
    """
    Create a basic fallback description when
    Hugging Face model card does not contain
    a usable description.
    """

    publisher = organization if organization else "an AI model publisher"

    return (
        f"{model_name} is an AI model published by "
        f"{publisher} and hosted on Hugging Face."
    )


# ============================================================
# GET LOGO URL
# ============================================================

def get_logo_url(organization):
    """
    Get the official Hugging Face organization avatar.
    """

    if not organization:
        return ""

    return (
        f"https://huggingface.co/api/organizations/"
        f"{organization}/avatar"
    )


# ============================================================
# ENRICH MODELS
# ============================================================

def enrich_models():

    # --------------------------------------------------------
    # Check input file
    # --------------------------------------------------------

    if not os.path.exists(INPUT_FILE):

        print("Input file not found:", INPUT_FILE)

        return

    # --------------------------------------------------------
    # Read models CSV
    # --------------------------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        models = list(reader)

    print("=" * 60)
    print("Starting Models Enrichment...")
    print("=" * 60)

    print(f"Models found: {len(models)}")

    enriched_records = []

    # --------------------------------------------------------
    # Process every model
    # --------------------------------------------------------

    for index, model in enumerate(models, start=1):

        model_name = model.get(
            "model_name",
            ""
        ).strip()

        organization = model.get(
            "organization",
            ""
        ).strip()

        # ----------------------------------------------------
        # Build model ID
        # ----------------------------------------------------

        if organization:

            model_id = (
                f"{organization}/{model_name}"
            )

        else:

            model_id = model_name

        print(
            f"[{index}/{len(models)}] "
            f"Processing: {model_id}"
        )

        # ----------------------------------------------------
        # Get description
        # ----------------------------------------------------

        description = get_description(
            model_id
        )

        # ----------------------------------------------------
        # Fallback if description is missing
        # ----------------------------------------------------

        if not description:

            print(
                f"   Description missing -> "
                f"using fallback"
            )

            description = create_fallback_description(
                model_name,
                organization
            )

        # ----------------------------------------------------
        # Get logo
        # ----------------------------------------------------

        logo_url = get_logo_url(
            organization
        )

        # ----------------------------------------------------
        # Official website
        #
        # Current source is the official Hugging Face
        # model page.
        # ----------------------------------------------------

        source_url = model.get(
            "source_url",
            ""
        ).strip()

        official_website = source_url

        # ----------------------------------------------------
        # Create enriched record
        # ----------------------------------------------------

        record = {

            "model_name": model_name,

            "organization": organization,

            "source_url": source_url,

            "official_website": official_website,

            "logo_url": logo_url,

            "description": description,

            "downloads": model.get(
                "downloads",
                0
            ),

            "likes": model.get(
                "likes",
                0
            ),

            "pipeline_tag": model.get(
                "pipeline_tag",
                ""
            ),

            "library_name": model.get(
                "library_name",
                ""
            )
        }

        enriched_records.append(record)

        # ----------------------------------------------------
        # Small delay
        # ----------------------------------------------------

        time.sleep(0.2)

    # ========================================================
    # CREATE DATA DIRECTORY
    # ========================================================

    os.makedirs(
        "data",
        exist_ok=True
    )

    # ========================================================
    # CSV COLUMNS
    # ========================================================

    fieldnames = [

        "model_name",

        "organization",

        "source_url",

        "official_website",

        "logo_url",

        "description",

        "downloads",

        "likes",

        "pipeline_tag",

        "library_name"
    ]

    # ========================================================
    # SAVE CSV
    # ========================================================

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

        writer.writerows(
            enriched_records
        )

    # ========================================================
    # COMPLETION
    # ========================================================

    print("=" * 60)
    print("MODELS ENRICHMENT COMPLETED")
    print("=" * 60)

    print(
        f"Models processed: "
        f"{len(enriched_records)}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    enrich_models()