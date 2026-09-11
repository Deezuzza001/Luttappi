import logging
import re

from pyrogram import Client, filters
from pyrogram.errors import RPCError

from info import FILE_CHANNELS
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


def get_file_channel_ids():
    """Return all configured FILE_CHANNELS as Telegram numeric channel IDs."""
    valid_ids = []
    for value in FILE_CHANNELS:
        try:
            channel_id = int(str(value).strip())
        except (TypeError, ValueError):
            LOGGER.error("❌ Invalid FILE_CHANNELS value: %r", value)
            continue
        if channel_id >= 0:
            LOGGER.error("❌ Invalid FILE_CHANNELS value: %s. Use -100... channel IDs.", channel_id)
            continue
        valid_ids.append(channel_id)
    return valid_ids


async def index_channel_history(client: Client):
    """Index existing files from all configured FILE_CHANNELS."""
    if not FILE_CHANNELS:
        LOGGER.error("❌ FILE_CHANNELS is not configured.")
        return

    channel_ids = get_file_channel_ids()
    if not channel_ids:
        LOGGER.error("❌ No valid FILE_CHANNELS configured.")
        return

    for channel_id in channel_ids:
        LOGGER.info("📂 Starting FILE_CHANNEL history indexing: %s", channel_id)
        try:
            channel = await client.get_chat(channel_id)
            LOGGER.info("✅ FILE_CHANNEL resolved: %s (%s)",
                        getattr(channel, "title", None) or "Unknown", channel.id)

            count = 0
            async for message in client.get_chat_history(channel_id):
                try:
                    if await save_channel_file(message):
                        count += 1
                        if count % 100 == 0:
                            LOGGER.info("📊 Channel %s: indexed %s files...", channel_id, count)
                except Exception:
                    LOGGER.exception("❌ Failed to index channel %s message %s",
                                     channel_id, message.id)

            LOGGER.info("✅ History indexing completed for %s. Total files: %s",
                        channel_id, count)
        except RPCError as e:
            LOGGER.error("❌ FILE_CHANNEL %s could not be resolved: %s. "
                         "Verify channel ID and bot membership.", channel_id, e)
        except Exception:
            LOGGER.exception("❌ Failed to read FILE_CHANNEL history for %s. "
                             "Verify channel ID and bot membership.", channel_id)


@Client.on_message(filters.channel & filters.media)
async def new_channel_file(client, message):
    """Automatically index newly uploaded files from any configured FILE_CHANNEL."""
    if not FILE_CHANNELS:
        return

    channel_ids = get_file_channel_ids()
    if message.chat.id not in channel_ids:
        return

    try:
        if await save_channel_file(message):
            LOGGER.info("✅ New FILE_CHANNEL file indexed: %s (channel %s)",
                        message.id, message.chat.id)
    except Exception:
        LOGGER.exception("❌ Failed to index new FILE_CHANNEL file %s (channel %s)",
                         message.id, message.chat.id)
