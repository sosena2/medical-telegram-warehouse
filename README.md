# Task 1 — Data Scraping and Collection

## Overview
This task builds a data scraping pipeline that extracts messages and images
from public Ethiopian medical Telegram channels and stores them in a
partitioned raw data lake.

## Channels Scraped
| Channel | Type |
|---|---|
| CheMed123 | Medical Products |
| tikvahpharma | Pharmaceuticals |
| lobelia_cosmetics | Cosmetics |
| DoctorsETBot | General Health |
| ethiopian_pharmacy | Pharmacy |

## Data Lake Structure
data/

└── raw/
├── telegram_messages/
│   └── YYYY-MM-DD/
│       └── channel_name.json
└── images/
└── channel_name/
└── message_id.jpg
## Fields Collected
| Field | Description |
|---|---|
| message_id | Unique Telegram message ID |
| channel_name | Name of the Telegram channel |
| message_date | Timestamp of the message |
| message_text | Full text content |
| has_media | Whether message contains media |
| image_path | Local path to downloaded image |
| views | Number of views |
| forwards | Number of times forwarded |

## Scripts
| Script | Purpose |
|---|---|
| `src/scraper.py` | Scrapes messages and images from Telegram |
| `src/load_to_postgres.py` | Loads JSON files into PostgreSQL raw schema |

## How to Run

### 1. Set up credentials in `.env`
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+251XXXXXXXXX
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=medical_warehouse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
### 2. Run the scraper
```bash
python src/scraper.py
```

### 3. Load data into PostgreSQL
```bash
python src/load_to_postgres.py
```

## Output
- Raw JSON files stored in `data/raw/telegram_messages/YYYY-MM-DD/`
- Images stored in `data/raw/images/channel_name/`
- Logs stored in `logs/`
- 576 records loaded into `raw.telegram_messages` in PostgreSQL

## Data Quality Issues Encountered
- Some channels were private or had changed usernames — handled with
  `ChannelPrivateError` exception
- Some messages had no text but contained media — kept if `has_media=True`
- Duplicate messages handled with `ON CONFLICT DO NOTHING` on insert
- Rate limiting handled with `FloodWaitError` and automatic wait

# Task 2 — Data Modeling and Transformation

## Overview
This task transforms raw Telegram message data into a clean, structured
data warehouse using dbt and a dimensional star schema optimized for
analytical queries.

## Design Decisions
- Used **MD5 hash** of channel name as surrogate key for `dim_channels`
  to avoid serial IDs that change across environments
- Used **MD5 hash** of channel_name + message_id as surrogate key for
  `fct_messages` to ensure uniqueness across channels
- `dim_dates` is generated from actual message dates rather than a full
  date spine to keep it lightweight
- Staging models are materialized as **views** to avoid data duplication
- Mart models are materialized as **tables** for query performance

## dbt Project Structure
medical_warehouse/

├── models/

│   ├── staging/

│   │   ├── sources.yml

│   │   └── stg_telegram_messages.sql

│   └── marts/

│       ├── dim_channels.sql

│       ├── dim_dates.sql

│       ├── fct_messages.sql

│       └── schema.yml

├── tests/

│   ├── assert_no_future_messages.sql

│   └── assert_positive_views.sql

├── dbt_project.yml

├── profiles.yml

└── packages.yml

## Models

### Staging
| Model | Description |
|---|---|
| `stg_telegram_messages` | Cleans and standardizes raw messages |

### Marts
| Model | Description |
|---|---|
| `dim_channels` | Channel dimension with stats and classification |
| `dim_dates` | Date dimension derived from message dates |
| `fct_messages` | Central fact table — one row per message |

## Data Cleaning Applied
- Removed messages with no text and no media
- Deduplicated messages by channel + message_id
- Cast all dates to TIMESTAMP
- Standardized channel names to lowercase
- Replaced NULL views/forwards with 0
- Added calculated fields: message_length, has_image flag

## How to Run

### 1. Install dbt packages
```bash
cd medical_warehouse
dbt deps
```

### 2. Run all models
```bash
dbt run
```

### 3. Run tests
```bash
dbt test
```

### 4. Generate and view documentation
```bash
dbt docs generate
dbt docs serve
```

## Tests
| Test | Type | Description |
|---|---|---|
| unique + not_null on PKs | Schema test | Ensures no duplicate or null keys |
| relationships on FKs | Schema test | Ensures referential integrity |
| assert_no_future_messages | Custom test | No messages with future dates |
| assert_positive_views | Custom test | No negative view counts |

