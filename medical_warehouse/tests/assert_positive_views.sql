-- Returns 0 rows = test passes
SELECT *
FROM {{ ref('fct_messages') }}
WHERE views < 0