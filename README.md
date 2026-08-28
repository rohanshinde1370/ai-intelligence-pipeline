# AI Intelligence Pipeline

An AI intelligence data ingestion and processing pipeline for collecting, validating, mapping, and analyzing data related to startups, products, research papers, news, and remote jobs.

## Project Overview

This project builds a structured intelligence pipeline that collects data from multiple sources and converts it into clean, normalized datasets.

The pipeline currently processes:

* Startups
* Products
* Research Papers
* News
* Remote Jobs
* Entity Relationships
* Entity Analytics
* Data Quality Validation

## Project Architecture

```text
Data Sources
     |
     v
  Crawlers
     |
     v
 CSV / JSON Datasets
     |
     v
 Entity Mapping
     |
     v
entity_relationships.csv
     |
     v
 Data Quality Check
     |
     v
 Entity Analytics
     |
     v
entity_analytics.csv
```

## Project Structure

```text
AI-Intelligence-Pipeline/
│
├── src/
│   ├── crawlers/
│   │   ├── github_lookup.py
│   │   ├── job_scraper.py
│   │   ├── news_scraper.py
│   │   ├── product_scraper.py
│   │   ├── research_paper_scraper.py
│   │   ├── research_pipeline.py
│   │   └── startup_scraper.py
│   │
│   └── processors/
│       ├── data_quality.py
│       ├── entity_analytics.py
│       └── entity_mapping.py
│
├── pipeline.py
├── startups.csv
├── research_papers.csv
├── README.md
└── .gitignore
```

## Data Collection

### Startups

* Records: **1000 startups**
* Source: Y Combinator

### Products

* Records: **1000 products**

### Research Papers

* Records: **1000 research papers**

### News

* Records: **25 news records**

### Remote Jobs

* Records collected: **100 fresh unique jobs**
* Freshness requirement: **24 hours**
* Successfully mapped to startups: **5 relationships**

## Entity Mapping

The entity mapping processor creates canonical startup entities and connects them with products, jobs, research papers, and news.

### Results

* **1000** canonical startup entities
* **1000** product relationships
* **5** job relationships
* **61** research paper relationships
* **17** news relationships

### Total

**1083 unique entity relationships**

### Relationship Types

```text
HAS_PRODUCT
HAS_JOB
MENTIONED_IN_RESEARCH
MENTIONED_IN_NEWS
```

Output:

```text
entity_relationships.csv
```

## Data Quality Validation

The data quality processor validates the generated datasets.

### Validation Results

| Dataset         | Records | Result |
| --------------- | ------: | ------ |
| Startups        |    1000 | PASS   |
| Products        |    1000 | PASS   |
| Research Papers |    1000 | PASS   |
| News            |      25 | PASS   |
| Jobs            |     100 | PASS   |

Additional checks:

* Missing required values: **0**
* Duplicate records: **0**
* Invalid confidence values: **0**
* Confidence validation: **PASS**

## Entity Analytics

The entity analytics processor aggregates relationship information for each canonical startup.

For every startup entity, the pipeline calculates:

* Product count
* Job count
* Research mention count
* News mention count
* Total relationships

### Analytics Result

* Entities analyzed: **1000**
* Input relationships: **1083**

Output:

```text
entity_analytics.csv
```

## Technologies Used

* Python
* Pandas
* aiohttp
* CSV / JSON
* REST APIs
* Web Scraping
* Regular Expressions
* Data Validation
* Entity Mapping
* Data Analytics
* Git & GitHub

## How to Run

### 1. Clone the repository

```bash
git clone https://github.com/rohanshinde1370/ai-intelligence-pipeline.git
cd ai-intelligence-pipeline
```

### 2. Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Run the pipeline

```powershell
python pipeline.py
```

### 5. Run individual processors

Entity mapping:

```powershell
python src\processors\entity_mapping.py
```

Data quality:

```powershell
python src\processors\data_quality.py
```

Entity analytics:

```powershell
python src\processors\entity_analytics.py
```

## Output Files

The pipeline generates structured CSV and JSON datasets including:

```text
jobs.csv
jobs.json
news.csv
news.json
products.csv
products.json
research_papers.csv
research_papers.json
entity_relationships.csv
entity_analytics.csv
```

Generated data files are excluded from Git tracking using `.gitignore`.

## Data Quality Status

```text
Data Quality Check: PASS
Entity Mapping: COMPLETED
Entity Analytics: COMPLETED
Pipeline Status: COMPLETED
```

## Author

**Rohan Shinde**

GitHub:
https://github.com/rohanshinde1370
