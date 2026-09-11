import logging
import re

from pyrogram import Client, filters
from pyrogram.errors import RPCError

from info import FILE_CHANNEL
from database.ia_filterdb import save_file
from utils import clean_file_name, normalize_query

LOGGER = logging.getLogger(__name__)


def get_file_info(message):
    """Get file name, size and type from a Telegram message."""
    if message.document:
        return message.document.file_name, message.document.file_size, "document"
    if message.video:
        return message.video.file_name, message.video.file_size, "video"
    if message.audio:
        return message.audio.file_name, message.audio.file_size, "audio"
    return None, 0, None


def get_search_name(file_name):
    """Create a clean searchable movie name."""
    name = clean_file_name(file_name)
    name = re.sub(
        r"\b(?:proper|repack|limited|extended|unrated|remastered)\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(r"\s+", " ", name).strip()
    return normalize_query(name)


async def save_channel_file(message):
    """Save a channel file into MongoDB."""
    file_name, file_size, file_type = get_file_info(message)
    if not file_name:
        return False

    file_data = {
        "chat_id": message.chat.id,
        "message_id": message.id,
        "file_name": file_name,
        "file_size": file_size,
        "file_type": file_type,
        "caption": message.caption or "",
        "search_name": get_search_name(file_name),
    }
    return await save_file(file_data)


def get_file_channel_id():
    """Return FILE_CHANNEL as a Telegram numeric channel ID."""
    try:
        channel_id = int(str(FILE_CHANNEL).strip())
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid FILE_CHANNEL: {FILE_CHANNEL!r}. "
            "Use the numeric channel ID, e.g. -1001234567890."
        )

    if channel_id >= 0:
        raise ValueError(
            f"Invalid FILE_CHANNEL: {channel_id}. "
            "For a channel, use its full numeric ID beginning with -100."
        )

    return channel_id


async def index_channel_history(client: Client):
    """Index existing files from FILE_CHANNEL using only its numeric ID."""
    if not FILE_CHANNEL:
        LOGGER.error("❌ FILE_CHANNEL is not configured.")
        return

    try:
        channel_id = get_file_channel_id()
    except ValueError as e:
        LOGGER.error("❌ %s", e)
        return

    LOGGER.info("📂 Starting FILE_CHANNEL history indexing: %s", channel_id)

    try:
        # Do NOT use get_dialogs(): Telegram bots cannot call messages.GetDialogs.
        channel = await client.get_chat(channel_id)
        LOGGER.info(
            "✅ FILE_CHANNEL resolved: %s (%s)",
            getattr(channel, "title", None) or "Unknown",
            channel.id,
        )

        count = 0
        async for message in client.get_chat_history(channel_id):
            try:
                if await save_channel_file(message):
                    count += 1
                    if count % 100 == 0:
                        LOGGER.info("📊 Indexed %s files...", count)
            except Exception:
                LOGGER.exception("❌ Failed to index message %s", message.id)

        LOGGER.info("✅ History indexing completed. Total files: %s", count)

    except RPCError as e:
        LOGGER.error(
            "❌ FILE_CHANNEL could not be resolved: %s. "
            "Verify that FILE_CHANNEL is the correct numeric channel ID "
            "(for example -1001234567890) and that the bot has been added "
            "to that channel. No get_dialogs() is used.",
            e,
        )
    except Exception:
        LOGGER.exception(
            "❌ Failed to read FILE_CHANNEL history. "
            "Verify the numeric channel ID and bot channel membership."
        )


@Client.on_message(filters.channel & filters.media)
async def new_channel_file(client, message):
    """Automatically index newly uploaded files from FILE_CHANNEL."""
    if not FILE_CHANNEL:
        return

    try:
        channel_id = get_file_channel_id()
    except ValueError:
        return

    if message.chat.id != channel_id:
        return

    try:
        if await save_channel_file(message):
            LOGGER.info("✅ New FILE_CHANNEL file indexed: %s", message.id)
    except Exception:
        LOGGER.exception("❌ Failed to index new FILE_CHANNEL file %s", message.id)
