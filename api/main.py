"""
FastAPI analytical API for the Medical Telegram Warehouse.
Exposes insights from the dbt mart tables.
"""

import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

from api.database import get_db
from api.schemas import (
    TopProduct, ChannelActivity,
    MessageResult, VisualContentStat
)

load_dotenv()

app = FastAPI(
    title="Medical Telegram Warehouse API",
    description="Analytical API for Ethiopian medical Telegram channel data",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "Medical Telegram Warehouse API is running"}


@app.get("/api/reports/top-products", response_model=List[TopProduct])
def get_top_products(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Returns the most frequently mentioned medical terms across all channels."""
    query = text("""
        SELECT
            word AS term,
            COUNT(*) AS mention_count
        FROM (
            SELECT regexp_split_to_table(
                LOWER(message_text), '\s+'
            ) AS word
            FROM marts.fct_messages
            WHERE message_text IS NOT NULL
              AND LENGTH(message_text) > 2
        ) words
        WHERE LENGTH(word) > 3
          AND word NOT IN (
            'that','this','with','from','have',
            'will','your','they','been','were',
            'and','the','for','are','but','not',
            'you','all','can','her','was','one',
            'our','out','day','get','has','him'
          )
        GROUP BY word
        ORDER BY mention_count DESC
        LIMIT :limit
    """)
    rows = db.execute(query, {"limit": limit}).fetchall()
    return [{"term": r[0], "mention_count": r[1]} for r in rows]


@app.get("/api/channels/{channel_name}/activity", response_model=ChannelActivity)
def get_channel_activity(channel_name: str, db: Session = Depends(get_db)):
    """Returns posting activity and stats for a specific channel."""
    query = text("""
        SELECT
            channel_name,
            COUNT(*)                    AS total_posts,
            ROUND(AVG(views), 2)        AS avg_views,
            SUM(CASE WHEN has_image THEN 1 ELSE 0 END) AS total_images,
            MIN(message_date)           AS first_post_date,
            MAX(message_date)           AS last_post_date
        FROM marts.fct_messages
        WHERE LOWER(channel_name) = LOWER(:channel_name)
        GROUP BY channel_name
    """)
    row = db.execute(query, {"channel_name": channel_name}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Channel not found")
    return {
        "channel_name":    row[0],
        "total_posts":     row[1],
        "avg_views":       float(row[2] or 0),
        "total_images":    row[3],
        "first_post_date": row[4],
        "last_post_date":  row[5],
    }


@app.get("/api/search/messages", response_model=List[MessageResult])
def search_messages(
    query: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Searches for messages containing a specific keyword."""
    sql = text("""
        SELECT
            message_id,
            channel_name,
            message_text,
            views,
            forwards,
            message_date
        FROM marts.fct_messages
        WHERE LOWER(message_text) LIKE LOWER(:query)
        ORDER BY views DESC
        LIMIT :limit
    """)
    rows = db.execute(sql, {"query": f"%{query}%", "limit": limit}).fetchall()
    return [
        {
            "message_id":   r[0],
            "channel_name": r[1],
            "message_text": r[2],
            "views":        r[3] or 0,
            "forwards":     r[4] or 0,
            "message_date": r[5],
        }
        for r in rows
    ]


@app.get("/api/reports/visual-content", response_model=List[VisualContentStat])
def get_visual_content_stats(db: Session = Depends(get_db)):
    """Returns image usage statistics across all channels."""
    query = text("""
        SELECT
            channel_name,
            COUNT(*)                                        AS total_messages,
            SUM(CASE WHEN has_image THEN 1 ELSE 0 END)     AS messages_with_images,
            ROUND(
                100.0 * SUM(CASE WHEN has_image THEN 1 ELSE 0 END) / COUNT(*),
                2
            )                                               AS image_percentage
        FROM marts.fct_messages
        GROUP BY channel_name
        ORDER BY image_percentage DESC
    """)
    rows = db.execute(query).fetchall()
    return [
        {
            "channel_name":        r[0],
            "total_messages":      r[1],
            "messages_with_images": r[2],
            "image_percentage":    float(r[3] or 0),
        }
        for r in rows
    ]