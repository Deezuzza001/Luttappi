import asyncio
import logging
import os
import signal

from pyrogram import Client

from info import API_ID, API_HASH, BOT_TOKEN
from database import check_database
from database.ia_filterdb import create_indexes
from luttappi.indexer import index_channel_history


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------
# BOT
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# RENDER WEB SERVER
# ---------------------------------------------------------

async def start_health_server():
    """
    Render Web Service-ന് ഒരു HTTP port തുറന്ന് വെക്കാൻ
    ചെറിയ health server.
    """

    port = int(os.environ.get("PORT", "10000"))

    async def handle_client(reader, writer):
        try:
            await reader.read(4096)

            body = "Luttappi Running"

            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(body.encode('utf-8'))}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{body}"
            )

            writer.write(response.encode("utf-8"))
            await writer.drain()

        except Exception:
            pass

        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    server = await asyncio.start_server(
        handle_client,
        "0.0.0.0",
        port,
    )

    LOGGER.info(
        "🌐 Render health server started on port %s",
        port,
    )

    return server


# ---------------------------------------------------------
# DATABASE STARTUP
# ---------------------------------------------------------

async def startup():
    LOGGER.info("🔄 Checking MongoDB connection...")

    await check_database()

    LOGGER.info("✅ MongoDB connection successful.")

    await create_indexes()

    LOGGER.info("✅ Database indexes created.")


# ---------------------------------------------------------
# CHANNEL INDEXING
# ---------------------------------------------------------

async def safe_index_channel_history():
    """
    FILE_CHANNEL invalid ആയാലും indexing error കാരണം
    മുഴുവൻ bot process crash ആകരുത്.
    """

    try:
        await index_channel_history(app)

    except asyncio.CancelledError:
        LOGGER.info("🛑 Channel history indexing cancelled.")

    except Exception:
        LOGGER.exception(
            "❌ Channel history indexing failed. "
            "Bot will continue running."
        )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

async def main():

    # -----------------------------------------------------
    # START RENDER HEALTH SERVER FIRST
    # -----------------------------------------------------

    web_server = await start_health_server()

    index_task = None
    bot_started = False

    try:

        # -------------------------------------------------
        # DATABASE
        # -------------------------------------------------

        await startup()

        LOGGER.info(
            "🚀 Starting Luttappi Filter Bot..."
        )

        # -------------------------------------------------
        # START TELEGRAM BOT
        # -------------------------------------------------

        await app.start()

        bot_started = True

        me = await app.get_me()

        LOGGER.info(
            "🤖 Bot started as @%s",
            me.username,
        )

        # -------------------------------------------------
        # CHANNEL HISTORY INDEXING
        # -------------------------------------------------

        index_task = asyncio.create_task(
            safe_index_channel_history()
        )

        # -------------------------------------------------
        # STOP EVENT
        # -------------------------------------------------

        stop_event = asyncio.Event()

        def shutdown_handler():
            LOGGER.info(
                "🛑 Stop signal received..."
            )

            stop_event.set()

        loop = asyncio.get_running_loop()

        # -------------------------------------------------
        # RENDER SIGTERM
        # -------------------------------------------------

        try:
            loop.add_signal_handler(
                signal.SIGTERM,
                shutdown_handler,
            )

        except (
            NotImplementedError,
            RuntimeError,
        ):
            pass

        # -------------------------------------------------
        # CTRL+C / LOCAL SHUTDOWN
        # -------------------------------------------------

        try:
            loop.add_signal_handler(
                signal.SIGINT,
                shutdown_handler,
            )

        except (
            NotImplementedError,
            RuntimeError,
        ):
            pass

        # -------------------------------------------------
        # KEEP BOT RUNNING
        # -------------------------------------------------

        await stop_event.wait()

    except Exception:

        LOGGER.exception(
            "❌ Fatal error while running Luttappi Bot."
        )

        raise

    finally:

        LOGGER.info(
            "🛑 Stopping Luttappi Bot..."
        )

        # -------------------------------------------------
        # STOP INDEXING TASK
        # -------------------------------------------------

        if index_task is not None:

            if not index_task.done():

                index_task.cancel()

                try:
                    await index_task

                except asyncio.CancelledError:
                    pass

                except Exception:
                    LOGGER.exception(
                        "❌ Error stopping index task"
                    )

        # -------------------------------------------------
        # CLOSE RENDER HEALTH SERVER
        # -------------------------------------------------

        try:

            web_server.close()

            await web_server.wait_closed()

            LOGGER.info(
                "🌐 Render health server stopped."
            )

        except Exception:

            LOGGER.exception(
                "❌ Error stopping health server"
            )

        # -------------------------------------------------
        # STOP TELEGRAM BOT
        # -------------------------------------------------

        if bot_started:

            try:

                if app.is_connected:

                    await app.stop()

                    LOGGER.info(
                        "✅ Bot stopped successfully."
                    )

            except RuntimeError as e:

                # Prevent old Pyrogram loop error
                if "attached to a different loop" in str(e):

                    LOGGER.warning(
                        "⚠️ Pyrogram shutdown loop warning: %s",
                        e,
                    )

                else:

                    LOGGER.exception(
                        "❌ Error stopping Telegram bot"
                    )


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        LOGGER.info(
            "🛑 Bot stopped by user."
        )

    except Exception:

        LOGGER.exception(
            "❌ Bot stopped because of an unexpected error."
            )
