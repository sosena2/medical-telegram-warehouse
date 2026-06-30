"""
Loads YOLO detection results from CSV into raw.yolo_detections in PostgreSQL.
"""

import os
import csv
import logging
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "medical_warehouse"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def load_csv(path="data/processed/yolo_detections.csv"):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    logger.info(f"Read {len(rows)} rows from {path}")
    return rows


def insert_to_postgres(rows):
    if not rows:
        logger.warning("No rows to insert.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE SCHEMA IF NOT EXISTS raw;
        CREATE TABLE IF NOT EXISTS raw.yolo_detections (
            id                SERIAL PRIMARY KEY,
            message_id        BIGINT,
            channel_name      VARCHAR(255),
            image_path        VARCHAR(500),
            detected_class    VARCHAR(100),
            confidence_score  FLOAT,
            image_category    VARCHAR(50),
            detected_at       TIMESTAMP,
            loaded_at         TIMESTAMP DEFAULT NOW()
        );
    """)

    data = [(
        r["message_id"], r["channel_name"], r["image_path"],
        r["detected_class"], float(r["confidence_score"]),
        r["image_category"], r["detected_at"]
    ) for r in rows]

    execute_values(cur, """
        INSERT INTO raw.yolo_detections
            (message_id, channel_name, image_path, detected_class,
             confidence_score, image_category, detected_at)
        VALUES %s
    """, data)

    conn.commit()
    logger.info(f"Inserted {len(data)} rows into raw.yolo_detections")
    cur.close()
    conn.close()


if __name__ == "__main__":
    rows = load_csv()
    insert_to_postgres(rows)