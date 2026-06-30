# Medical Telegram Warehouse

An end-to-end data pipeline that extracts data from public Ethiopian medical
Telegram channels, transforms it into a clean analytical data warehouse using
dbt, enriches it with computer vision using YOLOv8, exposes insights through
a FastAPI REST API, and orchestrates the entire workflow with Dagster.

Built as part of the 10 Academy Data Engineering challenge: **"Shipping a
Data Product: From Raw Telegram Data to an Analytical API."**

---

## Business Need

Kara Solutions needs a data platform that turns raw Telegram chatter from
Ethiopian medical and pharmaceutical channels into actionable business
insight. This pipeline answers four core questions:

1. What are the top 10 most frequently mentioned medical products or drugs
   across all channels?
2. How does the price or availability of a specific product vary across
   different channels?
3. Which channels have the most visual content (e.g. images of pills vs.
   creams)?
4. What are the daily and weekly trends in posting volume for health-related
   topics?

---

## Architecture Overview

```
Telegram Channels
       │
       ▼
┌─────────────────┐
│   Task 1         │   Telethon scraper extracts messages + images
│   Extract & Load │   → JSON files in partitioned data lake
└────────┬─────────┘   → Loaded into raw.telegram_messages (PostgreSQL)
         ▼
┌─────────────────┐
│   Task 2         │   dbt cleans raw data into staging models
│   Transform      │   → Builds star schema: dim_channels, dim_dates,
│                  │     fct_messages
└────────┬─────────┘   → dbt tests validate data quality
         ▼
┌─────────────────┐
│   Task 3         │   YOLOv8 detects objects in downloaded images
│   Enrich         │   → Classifies images: promotional / product_display /
│                  │     lifestyle / other
└────────┬─────────┘   → fct_image_detections dbt model joins results
         ▼
┌─────────────────┐
│   Task 4         │   FastAPI exposes the warehouse via REST endpoints
│   Serve          │   → /docs auto-generated OpenAPI documentation
└────────┬─────────┘
         ▼
┌─────────────────┐
│   Task 5         │   Dagster orchestrates all steps as one scheduled,
│   Orchestrate    │   observable, daily pipeline with failure alerts
└─────────────────┘
```

---

## Project Structure

```
medical-telegram-warehouse/
├── .github/
│   └── workflows/
│       └── unittests.yml        # CI: runs pytest on every push
├── data/
│   ├── raw/
│   │   ├── telegram_messages/   # Partitioned JSON data lake
│   │   └── images/              # Downloaded Telegram images
│   └── processed/
│       └── yolo_detections.csv  # YOLO detection output
├── medical_warehouse/            # dbt project
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml
│   │   │   └── stg_telegram_messages.sql
│   │   └── marts/
│   │       ├── dim_channels.sql
│   │       ├── dim_dates.sql
│   │       ├── fct_messages.sql
│   │       ├── fct_image_detections.sql
│   │       └── schema.yml
│   ├── tests/
│   │   ├── assert_no_future_messages.sql
│   │   └── assert_positive_views.sql
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── packages.yml
├── src/
│   ├── scraper.py                # Task 1: Telegram scraper
│   ├── load_to_postgres.py       # Task 1: Raw data loader
│   ├── yolo_detect.py            # Task 3: YOLO object detection
│   └── load_yolo_results.py      # Task 3: YOLO results loader
├── api/
│   ├── main.py                   # Task 4: FastAPI application
│   ├── database.py               # Task 4: DB connection (SQLAlchemy)
│   └── schemas.py                # Task 4: Pydantic models
├── pipeline.py                   # Task 5: Dagster ops and job
├── definitions.py                # Task 5: Dagster entry point
├── scripts/
│   └── init_db.sql               # PostgreSQL schema bootstrap
├── tests/
│   └── test_pipeline.py          # Unit tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

---

## Branch Strategy

Each task was developed on its own feature branch, built on top of the
previous one, and merged into `main` via pull request.

| Branch | Contents |
|---|---|
| `main` | Project scaffold, Docker setup, CI workflow |
| `feature/task-1-scraping` | Telegram scraper, data lake, raw loader |
| `feature/task-2-dbt` | Staging models, star schema, dbt tests |
| `feature/task-3-yolo` | YOLO detection, image classification, enrichment model |
| `feature/task-4-api` | FastAPI endpoints, Pydantic schemas |
| `feature/task-5-dagster` | Pipeline orchestration, scheduling, failure alerts |

---

## Tech Stack

| Layer | Tool |
|---|---|
| Extraction | Telethon (Telegram API) |
| Storage | PostgreSQL |
| Transformation | dbt |
| Enrichment | YOLOv8 (Ultralytics) |
| API | FastAPI + SQLAlchemy + Pydantic |
| Orchestration | Dagster |
| Containerization | Docker, Docker Compose |
| CI | GitHub Actions |

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/medical-telegram-warehouse.git
cd medical-telegram-warehouse
```

### 2. Create and activate a virtual environment
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in your credentials:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+251XXXXXXXXX

POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=medical_warehouse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

Get Telegram credentials at **my.telegram.org → API development tools**.

### 5. Start PostgreSQL
```bash
docker-compose up -d postgres
```

---

## Running the Pipeline (Step by Step)

### Task 1 — Scrape and load raw data
```bash
python src/scraper.py
python src/load_to_postgres.py
```

### Task 2 — Transform with dbt
```bash
cd medical_warehouse
dbt deps
dbt run
dbt test
dbt docs generate
dbt docs serve
cd ..
```

### Task 3 — Enrich with YOLO
```bash
python src/yolo_detect.py
python src/load_yolo_results.py
cd medical_warehouse
dbt run --select fct_image_detections
cd ..
```

### Task 4 — Serve the API
```bash
uvicorn api.main:app --reload
```
Visit `http://127.0.0.1:8000/docs` for interactive API documentation.

### Task 5 — Orchestrate with Dagster
```bash
dagster dev -f definitions.py
```
Visit `http://localhost:3000` to run and monitor the pipeline.

---

## Data Warehouse — Star Schema

```
                    ┌─────────────┐
                    │  dim_dates  │
                    └──────┬──────┘
                           │
┌──────────────┐    ┌──────┴────────┐    ┌────────────────────┐
│ dim_channels ├────┤  fct_messages ├────┤ fct_image_detections│
└──────────────┘    └───────────────┘    └────────────────────┘
```

- **dim_channels** — channel metadata, type classification, posting stats
- **dim_dates** — calendar attributes derived from message dates
- **fct_messages** — one row per Telegram message, the central fact table
- **fct_image_detections** — YOLO detection results joined to messages

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/reports/top-products?limit=10` | Most frequently mentioned products |
| `GET /api/channels/{channel_name}/activity` | Posting activity for a channel |
| `GET /api/search/messages?query=paracetamol` | Keyword search across messages |
| `GET /api/reports/visual-content` | Image usage statistics by channel |

Full interactive documentation is available at `/docs` when the API is running.

---

## Testing

```bash
pytest tests/ -v
```

CI runs automatically on every push via `.github/workflows/unittests.yml`.

dbt data quality tests:
```bash
cd medical_warehouse
dbt test
```

---

## Known Limitations

- YOLOv8 is a general-purpose object detector and does not recognize
  specific pharmaceutical products by name — it classifies images based on
  generic object classes (person, bottle, box, etc.)
- Only `tikvahpharma` and `CheMed123` were successfully scraped in the
  current dataset; `lobelia_cosmetics` and other listed channels were
  private or unavailable at scrape time
- Mixed Amharic/English content in message text affects keyword-based
  product search accuracy

---
