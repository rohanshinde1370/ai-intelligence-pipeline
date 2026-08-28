import subprocess
import sys


def run_step(name, script):

    print()
    print("=" * 50)
    print(f"Running: {name}")
    print("=" * 50)

    result = subprocess.run(
        [sys.executable, script]
    )

    if result.returncode != 0:

        print()
        print(f"{name} FAILED")

        sys.exit(result.returncode)

    print()
    print(f"{name} COMPLETED")


def main():

    print("=" * 50)
    print("AI INTELLIGENCE PIPELINE")
    print("=" * 50)

    run_step(
        "Job Scraper",
        "src/crawlers/job_scraper.py"
    )

    run_step(
        "Entity Mapping",
        "src/processors/entity_mapping.py"
    )

    run_step(
        "Data Quality Check",
        "src/processors/data_quality.py"
    )

    run_step(
        "Entity Analytics",
        "src/processors/entity_analytics.py"
    )

    print()
    print("=" * 50)
    print("FULL PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 50)


if __name__ == "__main__":
    main()