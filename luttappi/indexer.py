import logging
import re

from pyrogram import Client, filters

from info import FILE_CHANNEL
from database.ia_filterdb import save_file
from utils import clean_file_name, normalize_query

LOGGER = logging.getLogger(__name__)


def get_file_info(message):
    """Get file name, size and type from a Telegram message."""

    if message.document:
        return (
            message.document.file_name,
            message.document.file_size,
            "document",
        )

    if message.video:
        return (
            message.video.file_name,
            message.video.file_size,
            "video",
        )

    if message.audio:
        return (
            message.audio.file_name,
            message.audio.file_size,
            "audio",
        )

    return None, 0, None


def get_search_name(file_name):
    """Create a clean searchable movie name."""

    name = clean_file_name(file_name)

    # Remove common release tags
    name = re.sub(
        r"\b(?:proper|repack|limited|extended|unrated|remastered)\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )

    # Remove extra spaces
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


async def index_channel_history(client: Client):
    """
    Index all existing files from FILE_CHANNEL.
    """

    if not FILE_CHANNEL:
        LOGGER.error("❌ FILE_CHANNEL is not configured.")
        return

    LOGGER.info(
        "📂 Starting FILE_CHANNEL history indexing: %s",
        FILE_CHANNEL,
    )

    count = 0

    try:
        # Resolve through dialogs first. This helps Pyrogram know private
        # channel peers when FILE_CHANNEL is stored only as a -100... ID.
        channel = None

        async for dialog in client.get_dialogs():
            if dialog.chat and dialog.chat.id == FILE_CHANNEL:
                channel = dialog.chat
                break

        if channel is None:
            try:
                channel = await client.get_chat(FILE_CHANNEL)
            except Exception:
                channel = None

        if channel is None:
            LOGGER.error(
                "❌ FILE_CHANNEL %s could not be resolved. "
                "Check the channel ID and make sure the bot has joined it.",
                FILE_CHANNEL,
            )
            return

        channel_id = channel.id

        LOGGER.info(
            "✅ FILE_CHANNEL resolved: %s (%s)",
            getattr(channel, "title", None) or "Unknown",
            channel_id,
        )

        async for message in client.get_chat_history(channel_id):

            try:
                if await save_channel_file(message):
                    count += 1

                    if count % 100 == 0:
                        LOGGER.info(
                            "📊 Indexed %s files...",
                            count,
                        )

            except Exception:
                LOGGER.exception(
                    "❌ Failed to index message %s",
                    message.id,
                )

    except Exception:
        LOGGER.exception(
            "❌ Failed to read FILE_CHANNEL history. "
            "Check that the bot is a member/admin and FILE_CHANNEL is correct."
        )

    LOGGER.info(
        "✅ History indexing completed. Total files: %s",
        count,
    )


@Client.on_message(filters.channel & filters.media)
async def new_channel_file(client, message):
    """
    Automatically index newly uploaded files.
    """

    if not FILE_CHANNEL:
        return

    if message.chat.id != FILE_CHANNEL:
        return

    try:
        if await save_channel_file(message):
            LOGGER.info(
                "✅ New FILE_CHANNEL file indexed: %s",
                message.id,
            )

    except Exception:
        LOGGER.exception(
            "❌ Failed to index new FILE_CHANNEL file %s",
            message.id,
        )
