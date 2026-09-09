import asyncio
import logging
import re

from pyrogram import Client

from info import API_ID, API_HASH, BOT_TOKEN, FILE_CHANNEL
from database.ia_filterdb import save_file
from utils import clean_file_name, normalize_query


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

LOGGER = logging.getLogger(__name__)


app = Client(
    "AdvancedAutoFilterIndexer",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


def get_file_info(message):

    if message.document:
        return (
            message.document.file_name,
            message.document.file_size,
            "document"
        )

    if message.video:
        return (
            message.video.file_name,
            message.video.file_size,
            "video"
        )

    if message.audio:
        return (
            message.audio.file_name,
            message.audio.file_size,
            "audio"
        )

    return None, 0, None


def get_search_name(file_name):

    name = clean_file_name(file_name)

    # Remove common release tags
    name = re.sub(
        r"\b(?:proper|repack|limited|extended|unrated|remastered)\b",
        " ",
        name,
        flags=re.IGNORECASE
    )

    name = re.sub(r"\s+", " ", name)

    return normalize_query(name)


async def index_channel():

    if not FILE_CHANNEL:
        LOGGER.error("❌ FILE_CHANNEL is not configured.")
        return

    LOGGER.info(
        "📂 Starting indexing for channel: %s",
        FILE_CHANNEL
    )

    count = 0

    async for message in app.get_chat_history(FILE_CHANNEL):

        file_name, file_size, file_type = get_file_info(message)

        if not file_name:
            continue

        search_name = get_search_name(file_name)

        data = {
            "chat_id": message.chat.id,
            "message_id": message.id,
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type,
            "caption": message.caption or "",
            "search_name": search_name,
        }

        saved = await save_file(data)

        if saved:
            count += 1

        if count % 100 == 0 and count:
            LOGGER.info(
                "📊 Indexed %s files...",
                count
            )

    LOGGER.info(
        "✅ Indexing completed. Total: %s",
        count
    )


async def main():

    await app.start()

    try:
        await index_channel()
    except Exception as error:
        LOGGER.exception(
            "❌ Indexing error: %s",
            error
        )
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
