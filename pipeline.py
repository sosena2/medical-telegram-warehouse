"""
pipeline.py
Dagster pipeline orchestrating the full Medical Telegram Warehouse workflow:
scrape -> load raw -> dbt transform -> YOLO enrichment -> load YOLO results
"""

import os
import subprocess
import asyncio
from pathlib import Path

from dagster import (
    op, job, In, Out, Nothing,
    ScheduleDefinition, DefaultScheduleStatus,
    OpExecutionContext, Failure, RetryPolicy,
)

PROJECT_ROOT = Path(__file__).parent
DBT_PROJECT_DIR = PROJECT_ROOT / "medical_warehouse"


# ── Op 1: Scrape Telegram data ───────────────────────────────────────────
@op(retry_policy=RetryPolicy(max_retries=2, delay=30))
def scrape_telegram_data(context: OpExecutionContext) -> Nothing:
    """Runs the Telegram scraper to collect messages and images."""
    context.log.info("Starting Telegram scrape...")

    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.scraper import main as scraper_main

    try:
        asyncio.run(scraper_main())
        context.log.info("Telegram scrape completed successfully.")
    except Exception as e:
        context.log.error(f"Scraping failed: {e}")
        raise Failure(description=f"Telegram scraping failed: {e}")


# ── Op 2: Load raw JSON to PostgreSQL ────────────────────────────────────
@op(ins={"start": In(Nothing)})
def load_raw_to_postgres(context: OpExecutionContext) -> Nothing:
    """Loads scraped JSON files from the data lake into PostgreSQL raw schema."""
    context.log.info("Loading raw data into PostgreSQL...")

    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.load_to_postgres import load_json_files, insert_to_postgres

    try:
        records = load_json_files()
        insert_to_postgres(records)
        context.log.info(f"Loaded {len(records)} records into raw.telegram_messages")
    except Exception as e:
        context.log.error(f"Loading to PostgreSQL failed: {e}")
        raise Failure(description=f"PostgreSQL load failed: {e}")


# ── Op 3: Run dbt transformations ────────────────────────────────────────
@op(ins={"start": In(Nothing)})
def run_dbt_transformations(context: OpExecutionContext) -> Nothing:
    """Runs dbt models and tests to transform raw data into the star schema."""
    context.log.info("Running dbt transformations...")

    env = os.environ.copy()

    run_result = subprocess.run(
        ["dbt", "run"],
        cwd=str(DBT_PROJECT_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    context.log.info(run_result.stdout)

    if run_result.returncode != 0:
        context.log.error(run_result.stderr)
        raise Failure(description="dbt run failed")

    test_result = subprocess.run(
        ["dbt", "test"],
        cwd=str(DBT_PROJECT_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    context.log.info(test_result.stdout)

    if test_result.returncode != 0:
        context.log.error(test_result.stderr)
        raise Failure(description="dbt test failed — data quality checks did not pass")

    context.log.info("dbt run and test completed successfully.")


# ── Op 4: Run YOLO enrichment ────────────────────────────────────────────
@op(ins={"start": In(Nothing)})
def run_yolo_enrichment(context: OpExecutionContext) -> Nothing:
    """Runs YOLOv8 object detection on downloaded images and loads results to PostgreSQL."""
    context.log.info("Running YOLO object detection...")

    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.yolo_detect import run_detection
    from src.load_yolo_results import load_csv, insert_to_postgres as insert_yolo

    try:
        run_detection()
        rows = load_csv()
        insert_yolo(rows)
        context.log.info(f"YOLO enrichment completed. {len(rows)} detection rows loaded.")
    except Exception as e:
        context.log.error(f"YOLO enrichment failed: {e}")
        raise Failure(description=f"YOLO enrichment failed: {e}")


# ── Op 5: Rebuild image detections mart ──────────────────────────────────
@op(ins={"start": In(Nothing)})
def run_dbt_image_detections(context: OpExecutionContext) -> Nothing:
    """Rebuilds the fct_image_detections model after YOLO results are loaded."""
    context.log.info("Rebuilding fct_image_detections...")

    env = os.environ.copy()
    result = subprocess.run(
        ["dbt", "run", "--select", "fct_image_detections"],
        cwd=str(DBT_PROJECT_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    context.log.info(result.stdout)

    if result.returncode != 0:
        context.log.error(result.stderr)
        raise Failure(description="dbt run for fct_image_detections failed")

    context.log.info("fct_image_detections rebuilt successfully.")


# ── Job: Define execution graph ──────────────────────────────────────────
@job(
    description="Full Medical Telegram Warehouse pipeline: scrape -> load -> "
                 "transform -> enrich -> rebuild marts"
)
def medical_warehouse_pipeline():
    scraped = scrape_telegram_data()
    loaded = load_raw_to_postgres(start=scraped)
    transformed = run_dbt_transformations(start=loaded)
    enriched = run_yolo_enrichment(start=transformed)
    run_dbt_image_detections(start=enriched)


# ── Schedule: Run daily ──────────────────────────────────────────────────
daily_schedule = ScheduleDefinition(
    job=medical_warehouse_pipeline,
    cron_schedule="0 6 * * *",  # Every day at 06:00 UTC
    default_status=DefaultScheduleStatus.STOPPED,  # Start as STOPPED; enable manually in UI
    execution_timezone="UTC",
)