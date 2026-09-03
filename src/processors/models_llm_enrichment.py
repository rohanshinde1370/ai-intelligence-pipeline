import csv
import os
import time
from dotenv import load_dotenv
from google import genai

# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=API_KEY)

# --------------------------------------------------
# FILES
# --------------------------------------------------

INPUT_FILE = "data/models_enriched.csv"
PROGRESS_FILE = "data/models_llm_progress.csv"
OUTPUT_FILE = "data/models_final.csv"
FAILED_FILE = "data/models_llm_failed.csv"

MODEL_NAME = "gemini-3.6-flash"

# --------------------------------------------------
# LLM DESCRIPTION
# --------------------------------------------------

def generate_description(model):

    model_name = model.get("model_name", "").strip()
    organization = model.get("organization", "").strip()
    pipeline = model.get("pipeline_tag", "").strip()
    library = model.get("library_name", "").strip()
    source_description = model.get("description", "").strip()

    prompt = f"""
You are creating a professional AI intelligence dataset.

Generate ONE concise, accurate description for the following AI model.

Model name: {model_name}
Organization: {organization}
Pipeline/task: {pipeline}
Library/framework: {library}

Existing source description:
{source_description}

Requirements:
- Write exactly 1 or 2 sentences.
- Clearly explain what this model is used for.
- Be factual and specific.
- Use the supplied information as the primary source.
- Do not invent capabilities, benchmarks, performance, or use cases.
- If information is limited, use a cautious description based only on the available metadata.
- Do not mention that you are an AI.
- Do not mention this prompt.
- Do not include URLs.
- Do not use bullet points.
- Avoid generic filler text.
"""

    max_retries = 3

    for attempt in range(1, max_retries + 1):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            description = response.text.strip()

            if description:
                return description

            print("Empty response received.")

        except Exception as e:

            error_text = str(e)

            print(
                f"Gemini error for {model_name} "
                f"(attempt {attempt}/{max_retries}): {error_text}"
            )

            # Retry temporary server/rate-limit errors
            temporary_errors = [
                "503",
                "429",
                "500",
                "502",
                "504",
                "UNAVAILABLE",
                "RESOURCE_EXHAUSTED"
            ]

            if any(error in error_text.upper() for error in temporary_errors):

                if attempt < max_retries:

                    wait_time = 5 * (2 ** (attempt - 1))

                    print(
                        f"Temporary error. Retrying in "
                        f"{wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue

            # Other errors -> don't retry
            break

    return ""


# --------------------------------------------------
# PROGRESS FILE
# --------------------------------------------------

def load_progress():

    progress = {}

    if not os.path.exists(PROGRESS_FILE):
        return progress

    with open(
        PROGRESS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            source_url = row.get("source_url", "").strip()
            description = row.get("description", "").strip()

            if source_url and description:
                progress[source_url] = description

    return progress


# --------------------------------------------------
# SAVE PROGRESS
# --------------------------------------------------

def save_progress(progress):

    os.makedirs("data", exist_ok=True)

    with open(
        PROGRESS_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "source_url",
                "description"
            ]
        )

        writer.writeheader()

        for source_url, description in progress.items():

            writer.writerow({
                "source_url": source_url,
                "description": description
            })


# --------------------------------------------------
# FAILED MODELS
# --------------------------------------------------

def save_failed(failed_models):

    os.makedirs("data", exist_ok=True)

    with open(
        FAILED_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "model_name",
                "organization",
                "source_url"
            ]
        )

        writer.writeheader()

        writer.writerows(failed_models)


# --------------------------------------------------
# FINAL CSV
# --------------------------------------------------

def save_final(models, progress):

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

        for model in models:

            source_url = model.get(
                "source_url",
                ""
            ).strip()

            description = progress.get(
                source_url,
                ""
            )

            record = {
                "model_name": model.get(
                    "model_name",
                    ""
                ),

                "organization": model.get(
                    "organization",
                    ""
                ),

                "source_url": source_url,

                "official_website": model.get(
                    "official_website",
                    ""
                ),

                "logo_url": model.get(
                    "logo_url",
                    ""
                ),

                "description": description,

                "downloads": model.get(
                    "downloads",
                    ""
                ),

                "likes": model.get(
                    "likes",
                    ""
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

            writer.writerow(record)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def enrich_with_llm():

    if not os.path.exists(INPUT_FILE):

        print(
            "Input file not found:",
            INPUT_FILE
        )

        return

    # Load models
    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        models = list(reader)

    # Load previous progress
    progress = load_progress()

    print("=" * 60)
    print("STARTING LLM MODEL DESCRIPTION GENERATION")
    print("=" * 60)

    print(
        f"Total models: {len(models)}"
    )

    print(
        f"Already completed: {len(progress)}"
    )

    remaining = len(models) - len(progress)

    print(
        f"Remaining: {remaining}"
    )

    print("=" * 60)

    failed_models = []

    try:

        for index, model in enumerate(
            models,
            start=1
        ):

            model_name = model.get(
                "model_name",
                ""
            ).strip()

            source_url = model.get(
                "source_url",
                ""
            ).strip()

            # ------------------------------------------
            # SKIP COMPLETED MODEL
            # ------------------------------------------

            if source_url in progress:

                print(
                    f"[{index}/{len(models)}] "
                    f"SKIP: {model_name}"
                )

                continue

            print(
                f"[{index}/{len(models)}] "
                f"Generating: {model_name}"
            )

            # ------------------------------------------
            # GENERATE DESCRIPTION
            # ------------------------------------------

            description = generate_description(
                model
            )

            # ------------------------------------------
            # SUCCESS
            # ------------------------------------------

            if description:

                progress[source_url] = description

                # IMPORTANT:
                # Save immediately
                save_progress(progress)

                print(
                    f"SUCCESS: {model_name}"
                )

            # ------------------------------------------
            # FAILURE
            # ------------------------------------------

            else:

                print(
                    f"FAILED: {model_name}"
                )

                failed_models.append({
                    "model_name": model_name,
                    "organization": model.get(
                        "organization",
                        ""
                    ),
                    "source_url": source_url
                })

                save_failed(
                    failed_models
                )

            # Small delay
            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print("=" * 60)
        print("PROCESS INTERRUPTED")
        print("=" * 60)

        print(
            f"Progress saved: {len(progress)}"
        )

        print(
            "Run the same command again to resume."
        )

        return

    # ------------------------------------------
    # FINAL OUTPUT
    # ------------------------------------------

    print()
    print("=" * 60)
    print("LLM GENERATION FINISHED")
    print("=" * 60)

    print(
        f"LLM descriptions generated: "
        f"{len(progress)} / {len(models)}"
    )

    # Only create final CSV when every model
    # has an LLM-generated description

    if len(progress) == len(models):

        save_final(
            models,
            progress
        )

        print()
        print("SUCCESS: All models completed.")
        print(
            f"Final output: {OUTPUT_FILE}"
        )

    else:

        print()
        print(
            "WARNING: Some models are still missing."
        )

        print(
            f"Completed: {len(progress)}"
        )

        print(
            f"Missing: {len(models) - len(progress)}"
        )

        print()
        print(
            "Run the script again later."
        )

    print("=" * 60)


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    enrich_with_llm()