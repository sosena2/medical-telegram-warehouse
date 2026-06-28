"""
Reads JSON files from the data lake and loads them
into raw.telegram_messages in PostgreSQL.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            f"logs/loader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "medical_warehouse"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def load_json_files(path="data/raw/telegram_messages"):
    all_records = []
    for json_file in Path(path).rglob("*.json"):
        logger.info(f"Reading: {json_file}")
        with open(json_file, "r", encoding="utf-8") as f:
            all_records.extend(json.load(f))
    logger.info(f"Total records: {len(all_records)}")
    return all_records


def insert_to_postgres(records):
    if not records:
        logger.warning("No records to insert.")
        return

    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        CREATE SCHEMA IF NOT EXISTS raw;
        CREATE TABLE IF NOT EXISTS raw.telegram_messages (
            id            SERIAL PRIMARY KEY,
            message_id    BIGINT,
            channel_name  VARCHAR(255),
            message_date  TIMESTAMP,
            message_text  TEXT,
            has_media     BOOLEAN DEFAULT FALSE,
            image_path    VARCHAR(500),
            views         INTEGER DEFAULT 0,
            forwards      INTEGER DEFAULT 0,
            scraped_at    TIMESTAMP,
            loaded_at     TIMESTAMP DEFAULT NOW()
        );
    """)

    rows = [(
        r.get("message_id"),
        r.get("channel_name"),
        r.get("message_date"),
        r.get("message_text", ""),
        r.get("has_media", False),
        r.get("image_path"),
        r.get("views", 0),
        r.get("forwards", 0),
        r.get("scraped_at"),
    ) for r in records]

    execute_values(cur, """
        INSERT INTO raw.telegram_messages
            (message_id, channel_name, message_date, message_text,
             has_media, image_path, views, forwards, scraped_at)
        VALUES %s
        ON CONFLICT DO NOTHING
    """, rows)

    conn.commit()
    logger.info(f"Inserted {len(rows)} records.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    records = load_json_files()
    insert_to_postgres(records)