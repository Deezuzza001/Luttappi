import asyncio
import logging

from pyrogram import Client, idle

from info import API_ID, API_HASH, BOT_TOKEN
from database import check_database
from database.ia_filterdb import create_indexes
from luttappi.indexer import index_channel_history

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

LOGGER = logging.getLogger(__name__)


class LuttappiFilterBot(Client):
    def __init__(self):
        super().__init__(
            name="LuttappiFilterBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins={"root": "luttappi"},
            workers=32,
            sleep_threshold=30,
        )


app = LuttappiFilterBot()


async def startup():
    LOGGER.info("🔄 Checking MongoDB connection...")
    await check_database()
    LOGGER.info("✅ MongoDB connection successful.")

    await create_indexes()
    LOGGER.info("✅ Database indexes created.")


async def main():
    await startup()
    LOGGER.info("🚀 Starting Luttappi Filter Bot...")

    await app.start()
    me = await app.get_me()
    LOGGER.info("🤖 Bot started as @%s", me.username)

    # Run indexing on the same event loop as the Pyrogram client.
    index_task = asyncio.create_task(index_channel_history(app))

    try:
        await idle()
    finally:
        LOGGER.info("🛑 Stopping bot...")

        if not index_task.done():
            index_task.cancel()
            try:
                await index_task
            except asyncio.CancelledError:
                pass

        # Avoid failing shutdown if Render sends SIGTERM while Pyrogram is
        # already stopping its dispatcher.
        try:
            await app.stop()
        except RuntimeError as e:
            if "attached to a different loop" in str(e):
                LOGGER.warning("⚠️ Pyrogram shutdown loop warning: %s", e)
            else:
                raise


if __name__ == "__main__":
    asyncio.run(main())
