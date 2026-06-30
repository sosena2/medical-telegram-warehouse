{{ config(materialized='table') }}

WITH detections AS (
    SELECT
        CAST(message_id AS BIGINT)      AS message_id,
        channel_name,
        image_path,
        detected_class,
        CAST(confidence_score AS FLOAT) AS confidence_score,
        image_category,
        CAST(detected_at AS TIMESTAMP)  AS detected_at
    FROM {{ source('raw', 'yolo_detections') }}
),

messages AS (
    SELECT message_key, message_id, channel_key, date_key
    FROM {{ ref('fct_messages') }}
)

SELECT
    d.message_id,
    m.channel_key,
    m.date_key,
    d.detected_class,
    d.confidence_score,
    d.image_category,
    d.image_path,
    d.detected_at
FROM detections d
LEFT JOIN messages m ON d.message_id = m.message_id