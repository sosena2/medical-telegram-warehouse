import psycopg2

conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    dbname='medical_warehouse',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

tables = [
    'staging_staging.stg_telegram_messages',
    'staging_marts.dim_channels',
    'staging_marts.dim_dates',
    'staging_marts.fct_messages',
    'raw.telegram_messages',
]

for table in tables:
    cur.execute(f'SELECT COUNT(*) FROM {table}')
    print(f'{table}: {cur.fetchone()[0]} records')

conn.close()