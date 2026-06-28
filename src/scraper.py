"""
Telegram scraper for Ethiopian medical business channels.
Extracts messages and images, stores them in a partitioned data lake.
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError
from dotenv import load_dotenv

load_dotenv()

API_ID   = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE    = os.getenv("TELEGRAM_PHONE", "")

CHANNELS = [
    "CheMed123",
    "lobelia_cosmetics",
    "tikvahpharma",
    "DoctorsETBot",
    "ethiopian_pharmacy",
]

DATA_LAKE_PATH = Path("data/raw/telegram_messages")
IMAGES_PATH    = Path("data/raw/images")
LOGS_PATH      = Path("logs")

LOGS_PATH.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            LOGS_PATH / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


async def scrape_channel(client, channel, limit=500):
    messages = []
    logger.info(f"Starting scrape: {channel}")

    try:
        entity = await client.get_entity(channel)
        channel_display = entity.username or channel

        async for message in client.iter_messages(entity, limit=limit):
            try:
                msg_data = {
                    "message_id":   message.id,
                    "channel_name": channel_display,
                    "message_date": message.date.isoformat() if message.date else None,
                    "message_text": message.text or "",
                    "has_media":    message.media is not None,
                    "image_path":   None,
                    "views":        message.views or 0,
                    "forwards":     message.forwards or 0,
                    "scraped_at":   datetime.now(timezone.utc).isoformat(),
                }

                if message.photo:
                    img_dir = IMAGES_PATH / channel_display
                    img_dir.mkdir(parents=True, exist_ok=True)
                    img_file = img_dir / f"{message.id}.jpg"
                    if not img_file.exists():
                        await client.download_media(message.photo, file=str(img_file))
                        logger.info(f"  Downloaded image: {img_file}")
                    msg_data["image_path"] = str(img_file)

                messages.append(msg_data)

            except Exception as e:
                logger.warning(f"  Error on message {message.id}: {e}")
                continue

        logger.info(f"  Scraped {len(messages)} messages from {channel}")

    except ChannelPrivateError:
        logger.error(f"  Channel is private or not found: {channel}")
    except FloodWaitError as e:
        logger.warning(f"  Rate limited. Waiting {e.seconds}s...")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f"  Failed to scrape {channel}: {e}")

    return messages


def save_to_data_lake(channel, messages):
    if not messages:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    partition_dir = DATA_LAKE_PATH / today
    partition_dir.mkdir(parents=True, exist_ok=True)
    output_file = partition_dir / f"{channel}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"  Saved {len(messages)} messages to {output_file}")


async def main():
    logger.info("=" * 60)
    logger.info("Medical Telegram Warehouse — Scraper Started")
    logger.info("=" * 60)

    if not API_ID or not API_HASH:
        logger.error("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
        return

    DATA_LAKE_PATH.mkdir(parents=True, exist_ok=True)
    IMAGES_PATH.mkdir(parents=True, exist_ok=True)

    async with TelegramClient("session/telegram_session", API_ID, API_HASH) as client:
        await client.start(phone=PHONE)
        logger.info("Telegram client connected.")

        total = 0
        for channel in CHANNELS:
            messages = await scrape_channel(client, channel)
            if messages:
                save_to_data_lake(channel, messages)
                total += len(messages)
            await asyncio.sleep(2)

        logger.info(f"Done. Total messages scraped: {total}")


if __name__ == "__main__":
    Path("session").mkdir(exist_ok=True)
    asyncio.run(main())