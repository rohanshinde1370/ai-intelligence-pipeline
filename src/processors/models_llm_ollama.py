import csv
import os
import requests
import time

INPUT_FILE = "data/models_enriched.csv"
PROGRESS_FILE = "data/models_llm_progress.csv"
OUTPUT_FILE = "data/models_final.csv"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def generate_description(model):
    model_name = model.get("model_name", "").strip()
    organization = model.get("organization", "").strip()
    pipeline = model.get("pipeline_tag", "").strip()
    library = model.get("library_name", "").strip()

    prompt = f"""
You are creating a professional AI intelligence dataset.

Generate ONE concise and accurate description for this AI model.

Model name: {model_name}
Organization: {organization}
Pipeline/task: {pipeline}
Library/framework: {library}

Requirements:
- Write 1 to 2 sentences only.
- Clearly explain what the model is used for.
- Be specific and factual.
- Do not invent capabilities.
- Do not mention that you are an AI.
- Do not use bullet points.
- Do not include URLs.
- Avoid generic filler text.
- Return only the description.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()

        data = response.json()
        description = data.get("response", "").strip()

        if description:
            return description

    except Exception as e:
        print(f"Ollama error for {model_name}: {e}")

    return ""


def load_progress():
    progress = {}

    if not os.path.exists(PROGRESS_FILE):
        return progress

    with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            source_url = row.get("source_url", "").strip()
            description = row.get("description", "").strip()

            if source_url and description:
                progress[source_url] = description

    return progress


def save_progress(progress):
    os.makedirs("data", exist_ok=True)

    with open(PROGRESS_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["source_url", "description"]
        )

        writer.writeheader()

        for source_url, description in progress.items():
            writer.writerow({
                "source_url": source_url,
                "description": description
            })


def create_final_file(models, progress):
    os.makedirs("data", exist_ok=True)

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

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        for model in models:
            source_url = model.get("source_url", "").strip()

            row = dict(model)
            row["description"] = progress.get(source_url, "")

            writer.writerow(row)


def main():

    if not os.path.exists(INPUT_FILE):
        print("Input file not found:", INPUT_FILE)
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        models = list(csv.DictReader(file))

    progress = load_progress()

    print("=" * 60)
    print("OLLAMA MODEL DESCRIPTION GENERATION")
    print("=" * 60)
    print(f"Total models: {len(models)}")
    print(f"Already completed: {len(progress)}")
    print(f"Remaining: {len(models) - len(progress)}")
    print("=" * 60)

    for index, model in enumerate(models, start=1):

        source_url = model.get("source_url", "").strip()
        model_name = model.get("model_name", "").strip()

        # Skip already completed records
        if source_url in progress:
            print(f"[{index}/{len(models)}] SKIP: {model_name}")
            continue

        print(f"[{index}/{len(models)}] Generating: {model_name}")

        description = generate_description(model)

        if description:

            progress[source_url] = description

            save_progress(progress)

            print(f"SUCCESS: {model_name}")
            print(f"Progress saved: {len(progress)}")

        else:
            print(f"FAILED: {model_name}")

        # Small delay to avoid stressing local machine
        time.sleep(0.5)

    create_final_file(models, progress)

    print("=" * 60)
    print("OLLAMA ENRICHMENT COMPLETED")
    print("=" * 60)
    print(f"Descriptions generated: {len(progress)}")
    print(f"Final output: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()   