-- Returns 0 rows = test passes
SELECT *
FROM {{ ref('stg_telegram_messages') }}
WHERE message_date > NOW()