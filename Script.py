import asyncio
import logging

from pyrogram import Client

from info import API_ID, API_HASH, BOT_TOKEN, FILE_CHANNEL
from database.ia_filterdb import save_file

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


async def index_channel():
    if not FILE_CHANNEL:
        LOGGER.error("FILE_CHANNEL is not configured.")
        return

    LOGGER.info("Starting file indexing...")

    count = 0

    async for message in app.get_chat_history(FILE_CHANNEL):

        file_name = None
        file_size = 0

        if message.document:
            file_name = message.document.file_name
            file_size = message.document.file_size

        elif message.video:
            file_name = message.video.file_name
            file_size = message.video.file_size

        elif message.audio:
            file_name = message.audio.file_name
            file_size = message.audio.file_size

        if not file_name:
            continue

        data = {
            "chat_id": message.chat.id,
            "message_id": message.id,
            "file_name": file_name,
            "file_size": file_size,
            "caption": message.caption or "",
        }

        await save_file(data)

        count += 1

        if count % 100 == 0:
            LOGGER.info(
                "Indexed %s files...",
                count
            )

    LOGGER.info(
        "Indexing completed. Total files: %s",
        count
    )


async def main():
    await app.start()

    try:
        await index_channel()
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
