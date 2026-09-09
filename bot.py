import logging

from pyrogram import Client

from info import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
)

from database import check_database
from database.ia_filterdb import create_indexes


# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    )
)

LOGGER = logging.getLogger(__name__)


# =========================
# Bot Client
# =========================

class AdvancedAutoFilterBot(Client):

    def __init__(self):

        super().__init__(
            name="AdvancedAutoFilterBot",

            api_id=API_ID,
            api_hash=API_HASH,

            bot_token=BOT_TOKEN,

            plugins={
                "root": "luttappi"
            },

            workers=32,

            sleep_threshold=30,
        )


# =========================
# Create Bot
# =========================

app = AdvancedAutoFilterBot()


# =========================
# Startup
# =========================

async def startup():

    LOGGER.info(
        "Checking MongoDB connection..."
    )

    await check_database()

    LOGGER.info(
        "MongoDB connection successful."
    )

    await create_indexes()

    LOGGER.info(
        "Database indexes created."
    )


# =========================
# Run Bot
# =========================

if __name__ == "__main__":

    LOGGER.info(
        "Starting Advanced Auto Filter Bot..."
    )

    app.run(
        startup()
    )
