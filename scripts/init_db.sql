CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

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

CREATE INDEX IF NOT EXISTS idx_channel_name ON raw.telegram_messages(channel_name);
CREATE INDEX IF NOT EXISTS idx_message_date ON raw.telegram_messages(message_date);