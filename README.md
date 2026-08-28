# AI Intelligence Pipeline

AI intelligence data ingestion and extraction pipeline for collecting,
processing, validating, and analyzing data related to startups,
products, research papers, news, and jobs.
## Project Overview

This project collects and processes intelligence data from multiple
sources and converts it into structured datasets.

The pipeline currently handles:

- Startups
- Products
- Research Papers
- News
- Remote Jobs
- Entity Relationships
- Entity Analytics
- Data Quality Validation
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
## Project Structure

```text
AI-Intelligence-Pipeline/
│
├── src/
│   ├── crawlers/
│   └── processors/
│
├── startups.csv
├── startups.json
├── products.csv
├── products.json
├── research_papers.csv
├── research_papers.json
├── news.csv
├── news.json
├── jobs.csv
├── jobs.json
├── entity_relationships.csv
├── entity_analytics.csv
├── .gitignore
├── README.md
└── venv/
## Data Collection

The pipeline collects data from multiple sources and stores the
information in structured CSV and JSON files.

### Startups

Startup data is stored in:

- `startups.csv`
- `startups.json`

Records: **1000 startups**

### Products

Product data is stored in:

- `products.csv`
- `products.json`

Records: **1000 products**

### Research Papers

Research paper data is stored in:

- `research_papers.csv`
- `research_papers.json`

Records: **1000 research papers**

### News

News data is stored in:

- `news.csv`
- `news.json`

Records: **25 news records**

### Jobs

Remote job data is stored in:

- `jobs.csv`
- `jobs.json`

Records: **87 fresh unique jobs**
## Data Collection

The pipeline collects data from multiple sources and stores the
information in structured CSV and JSON files.

### Startups

Startup data is stored in:

- `startups.csv`
- `startups.json`

Records: **1000 startups**

### Products

Product data is stored in:

- `products.csv`
- `products.json`

Records: **1000 products**

### Research Papers

Research paper data is stored in:

- `research_papers.csv`
- `research_papers.json`

Records: **1000 research papers**

### News

News data is stored in:

- `news.csv`
- `news.json`

Records: **25 news records**

### Jobs

Remote job data is stored in:

- `jobs.csv`
- `jobs.json`

Records: **87 fresh unique jobs**
## Entity Mapping

The entity mapping process creates canonical startup entities and
connects them with products, jobs, research papers, and news.

The pipeline generated:

- **1000** canonical startup entities
- **1000** product relationships
- **5** job relationships
- **61** research paper relationships
- **17** news relationships

Total unique relationships: **1083**

Relationship types:

- `HAS_PRODUCT`
- `HAS_JOB`
- `MENTIONED_IN_RESEARCH`
- `MENTIONED_IN_NEWS`

The output is stored in:

`entity_relationships.csv`
## Data Quality Validation

A data quality validation process is used to verify required fields,
duplicate records, relationship counts, and confidence values.

Validation results:

- Products: **1000 rows**
- Research Papers: **1000 rows**
- News: **25 rows**
- Jobs: **87 rows**
- Missing required values: **0**
- Duplicate records: **0**
- Invalid confidence values: **0**

Data quality checks: **PASS**
## Data Quality Validation

A data quality validation process is used to verify required fields,
duplicate records, relationship counts, and confidence values.

Validation results:

- Products: **1000 rows**
- Research Papers: **1000 rows**
- News: **25 rows**
- Jobs: **87 rows**
- Missing required values: **0**
- Duplicate records: **0**
- Invalid confidence values: **0**

Data quality checks: **PASS**
## Entity Analytics

The entity analytics process aggregates relationship data for each
canonical startup entity.

For each startup, the pipeline calculates:

- Product count
- Job count
- Research mention count
- News mention count
- Total relationships

The analytics process analyzed **1000 entities** from **1083
relationships**.

The output is stored in:

`entity_analytics.csv`
## How to Run

### 1. Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1