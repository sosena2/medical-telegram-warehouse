WITH channel_stats AS (
    SELECT
        channel_name,
        COUNT(*)                                        AS total_posts,
        MIN(message_date)                               AS first_post_date,
        MAX(message_date)                               AS last_post_date,
        ROUND(AVG(views), 0)                            AS avg_views,
        SUM(CASE WHEN has_image THEN 1 ELSE 0 END)      AS total_images
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY channel_name
)

SELECT
    MD5(channel_name)       AS channel_key,
    channel_name,
    CASE
        WHEN channel_name ILIKE '%pharma%'          THEN 'Pharmaceutical'
        WHEN channel_name ILIKE '%cosmet%'
          OR channel_name ILIKE '%lobelia%'         THEN 'Cosmetics'
        WHEN channel_name ILIKE '%chem%'
          OR channel_name ILIKE '%med%'             THEN 'Medical'
        ELSE 'General Health'
    END                     AS channel_type,
    first_post_date,
    last_post_date,
    total_posts,
    avg_views,
    total_images
FROM channel_stats