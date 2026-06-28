WITH source AS (
    SELECT * FROM {{ source('raw', 'telegram_messages') }}
),

cleaned AS (
    SELECT
        id                                          AS surrogate_key,
        message_id,
        LOWER(TRIM(channel_name))                   AS channel_name,
        CAST(message_date AS TIMESTAMP)             AS message_date,
        DATE(message_date)                          AS message_day,
        TRIM(message_text)                          AS message_text,
        LENGTH(TRIM(COALESCE(message_text, '')))    AS message_length,
        has_media,
        CASE WHEN image_path IS NOT NULL
             THEN TRUE ELSE FALSE END               AS has_image,
        image_path,
        COALESCE(views, 0)                          AS views,
        COALESCE(forwards, 0)                       AS forwards,
        loaded_at
    FROM source
    WHERE
        (message_text IS NOT NULL AND TRIM(message_text) != '')
        OR has_media = TRUE
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY channel_name, message_id
            ORDER BY loaded_at DESC
        ) AS row_num
    FROM cleaned
)

SELECT * FROM deduplicated WHERE row_num = 1