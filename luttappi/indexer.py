import logging
import re

from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import ADMINS, FILE_CHANNELS
from database.ia_filterdb import save_file
from utils import clean_file_name, normalize_query


LOGGER = logging.getLogger(__name__)

# Pending manual indexing requests.
# request_id -> {
#     "requester_id": int,
#     "chat_id": int,
#     "message_id": int,
#     "file_chat_id": int,
#     "file_message_id": int,
#     "file_name": str,
# }
PENDING_INDEX_REQUESTS = {}


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


def _save_result_ok(result):
    """
    Normalize save_file() return values.

    Luttappi's database implementations may return either a boolean
    or EvaMaria-style tuples such as (saved, status).
    """
    if isinstance(result, tuple):
        return bool(result[0]) if result else False
    return bool(result)


def _save_result_status(result):
    """Return the optional second value from tuple-style save_file()."""
    if isinstance(result, tuple) and len(result) > 1:
        return result[1]
    return None


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

    result = await save_file(file_data)
    return _save_result_ok(result)


def get_file_channel_ids():
    """Return all configured FILE_CHANNELS as valid numeric Telegram IDs."""
    valid_ids = []

    for value in FILE_CHANNELS:
        try:
            channel_id = int(str(value).strip())
        except (TypeError, ValueError):
            LOGGER.error("❌ Invalid FILE_CHANNELS value: %r", value)
            continue

        if channel_id >= 0 or not str(channel_id).startswith("-100"):
            LOGGER.error(
                "❌ Invalid FILE_CHANNELS value: %s. Use -100... channel IDs.",
                channel_id,
            )
            continue

        if channel_id not in valid_ids:
            valid_ids.append(channel_id)

    return valid_ids


def is_admin(user_id):
    """Check whether a Telegram user can approve manual indexing."""
    try:
        return int(user_id) in {int(x) for x in ADMINS}
    except (TypeError, ValueError):
        return False


def _make_request_id(requester_id, chat_id, message_id):
    """Create a compact callback-safe request ID."""
    return f"{requester_id}:{chat_id}:{message_id}"


def _extract_forward_target(message):
    """
    Return (chat_id, message_id) for a forwarded channel message.

    Supports the Pyrogram fields used by the existing EvaMaria-style
    workflow.
    """
    chat = getattr(message, "forward_from_chat", None)
    msg_id = getattr(message, "forward_from_message_id", None)

    if chat and msg_id:
        return chat.id, msg_id

    # Compatibility with newer Telegram/Pyrogram forward-origin objects.
    origin = getattr(message, "forward_origin", None)
    if origin:
        origin_chat = getattr(origin, "chat", None)
        origin_msg_id = getattr(origin, "message_id", None)
        if origin_chat and origin_msg_id:
            return origin_chat.id, origin_msg_id

    return None, None


def _parse_telegram_link(text):
    """
    Parse a Telegram message link.

    Supported:
      https://t.me/channel/123
      https://t.me/c/1234567890/123
      https://telegram.me/channel/123
      https://telegram.dog/channel/123
    """
    if not text:
        return None, None

    pattern = re.compile(
        r"^(?:https?://)?"
        r"(?:t\.me|telegram\.me|telegram\.dog)/"
        r"(?:c/)?"
        r"([A-Za-z0-9_]+)/"
        r"(\d+)/?$",
        re.IGNORECASE,
    )

    match = pattern.match(text.strip())
    if not match:
        return None, None

    channel_ref = match.group(1)
    message_id = int(match.group(2))

    # Telegram private-channel /c/ links contain the channel's
    # internal numeric ID without the -100 prefix.
    if text.lower().replace("https://", "").replace("http://", "").find("/c/") != -1:
        try:
            channel_id = int(channel_ref)
            return int(f"-100{channel_id}"), message_id
        except ValueError:
            return None, None

    return channel_ref, message_id


async def _resolve_index_target(client, message):
    """Resolve a forwarded message or Telegram link to the real file message."""
    chat_id, message_id = _extract_forward_target(message)

    if chat_id and message_id:
        return chat_id, message_id

    if not message.text:
        return None, None

    return _parse_telegram_link(message.text)


async def _target_is_configured_channel(client, chat_id):
    """Check whether a target channel belongs to FILE_CHANNELS."""
    configured = get_file_channel_ids()
    if not configured:
        return False

    try:
        chat = await client.get_chat(chat_id)
        return int(chat.id) in configured
    except Exception:
        return False


async def _send_index_result(client, requester_id, text):
    """Best-effort confirmation to the user who submitted the request."""
    try:
        await client.send_message(requester_id, text)
    except Exception:
        LOGGER.exception("Could not send indexing result to user %s", requester_id)


async def _index_single_target(client, file_chat_id, file_message_id):
    """Fetch one channel message and add it to MongoDB."""
    message = await client.get_messages(file_chat_id, file_message_id)

    if not message or not get_file_info(message)[0]:
        return False, "unsupported", None

    file_name, _, _ = get_file_info(message)

    result = await save_file(
        {
            "chat_id": message.chat.id,
            "message_id": message.id,
            "file_name": file_name,
            "file_size": get_file_info(message)[1],
            "file_type": get_file_info(message)[2],
            "caption": message.caption or "",
            "search_name": get_search_name(file_name),
        }
    )

    if _save_result_ok(result):
        return True, "saved", file_name

    status = _save_result_status(result)

    # EvaMaria's save_file() convention:
    # status 0 = duplicate, status 2 = error.
    if status == 0:
        return False, "duplicate", file_name
    if status == 2:
        return False, "error", file_name

    return False, "not_saved", file_name


# ============================================================
# Existing channel history indexing
# ============================================================

async def _resolve_channel_peer(client: Client, channel_id: int):
    """Resolve a configured numeric Telegram channel ID.

    IMPORTANT:
    Pyrogram bot sessions cannot use messages.getDialogs() to discover
    arbitrary channel peers. A numeric -100... ID can only be used once
    Telegram has supplied the channel peer/access information to this
    session (normally when the bot is a member/admin and receives an update
    from that channel).

    We intentionally do NOT use get_dialogs() here.
    """
    try:
        chat = await client.get_chat(int(channel_id))

        if not chat:
            raise ValueError(f"Channel {channel_id} could not be resolved")

        LOGGER.info(
            "✅ FILE_CHANNEL resolved by ID: %s (%s)",
            getattr(chat, "title", None) or "Unknown",
            chat.id,
        )
        return chat

    except KeyError:
        LOGGER.error(
            "❌ Telegram peer is not cached for FILE_CHANNEL %s. "
            "The bot must be a member/admin of this channel and must have "
            "received at least one update/message from it. "
            "Numeric Channel ID support is enabled; usernames are not required.",
            channel_id,
        )
        raise

    except RPCError as e:
        LOGGER.error(
            "❌ Telegram rejected FILE_CHANNEL %s: %s. "
            "Check the numeric Channel ID and bot membership/admin access.",
            channel_id,
            e,
        )
        raise

    except Exception as e:
        LOGGER.error(
            "❌ Could not resolve FILE_CHANNEL %s by numeric ID: %s",
            channel_id,
            e,
        )
        raise


async def index_channel_history(client: Client):
    """Index existing files from all configured FILE_CHANNELS."""
    channel_ids = get_file_channel_ids()

    if not channel_ids:
        LOGGER.error("❌ FILE_CHANNELS is not configured or has no valid IDs.")
        return

    for channel_id in channel_ids:
        LOGGER.info("📂 Starting FILE_CHANNEL history indexing: %s", channel_id)

        try:
            channel = await _resolve_channel_peer(client, channel_id)
            resolved_id = int(channel.id)
            LOGGER.info(
                "✅ FILE_CHANNEL resolved: %s (%s)",
                getattr(channel, "title", None) or "Unknown",
                resolved_id,
            )

            count = 0

            async for message in client.get_chat_history(resolved_id):
                try:
                    if not get_file_info(message)[0]:
                        continue

                    if await save_channel_file(message):
                        count += 1

                        if count % 100 == 0:
                            LOGGER.info(
                                "📊 Channel %s: indexed %s files...",
                                channel_id,
                                count,
                            )

                except Exception:
                    LOGGER.exception(
                        "❌ Failed to index channel %s message %s",
                        channel_id,
                        message.id,
                    )

            LOGGER.info(
                "✅ History indexing completed for %s. Total new files: %s",
                channel_id,
                count,
            )

        except Exception:
            LOGGER.exception(
                "❌ Failed to read FILE_CHANNEL history for %s. "
                "Numeric Channel ID is supported, but Telegram has not "
                "provided a usable peer to this bot session yet. "
                "Make sure the bot is a member/admin and send a new message "
                "in the channel so the bot receives the channel update.",
                channel_id,
            )


# ============================================================
# Automatic indexing of NEW files
# ============================================================

@Client.on_message(filters.channel & filters.media)
async def new_channel_file(client, message):
    """Automatically index newly uploaded files from configured channels."""
    channel_ids = get_file_channel_ids()

    if not channel_ids or message.chat.id not in channel_ids:
        return

    try:
        if await save_channel_file(message):
            LOGGER.info(
                "✅ New FILE_CHANNEL file indexed: %s (channel %s)",
                message.id,
                message.chat.id,
            )
        else:
            LOGGER.info(
                "ℹ️ New FILE_CHANNEL file already exists or was not saved: "
                "%s (channel %s)",
                message.id,
                message.chat.id,
            )

    except Exception:
        LOGGER.exception(
            "❌ Failed to index new FILE_CHANNEL file %s (channel %s)",
            message.id,
            message.chat.id,
        )


# ============================================================
# EvaMaria-style: Forward / link -> Approve / Reject
# ============================================================

@Client.on_message(
    (filters.forwarded | (filters.regex(
        r"^(https://)?(t\.me/|telegram\.me/|telegram\.dog/)"
        r"(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$"
    ) & filters.text))
    & filters.private
    & filters.incoming
)
async def send_for_index(client, message):
    """
    Manual indexing workflow:

    1. User forwards a file from a configured FILE_CHANNEL
       or sends its Telegram message link.
    2. Admin gets Approve / Reject buttons.
    3. Approve saves that exact file into MongoDB.
    """
    try:
        file_chat_id, file_message_id = await _resolve_index_target(client, message)

        if not file_chat_id or not file_message_id:
            await message.reply_text(
                "❌ Valid channel message forward/link കണ്ടെത്താനായില്ല."
            )
            return

        if not await _target_is_configured_channel(client, file_chat_id):
            await message.reply_text(
                "❌ ഈ channel `FILE_CHANNELS`-ൽ configure ചെയ്തിട്ടില്ല."
            )
            return

        target = await client.get_messages(file_chat_id, file_message_id)
        file_name, _, _ = get_file_info(target)

        if not file_name:
            await message.reply_text(
                "❌ ഈ message-ൽ supported file ഇല്ല.\n"
                "Document / Video / Audio file അയക്കൂ."
            )
            return

        request_id = _make_request_id(
            message.from_user.id,
            int(file_chat_id),
            int(file_message_id),
        )

        PENDING_INDEX_REQUESTS[request_id] = {
            "requester_id": message.from_user.id,
            "chat_id": message.chat.id,
            "message_id": message.id,
            "file_chat_id": int(file_chat_id),
            "file_message_id": int(file_message_id),
            "file_name": file_name,
        }

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Accept",
                        callback_data=f"index#accept#{request_id}",
                    ),
                    InlineKeyboardButton(
                        "❌ Reject",
                        callback_data=f"index#reject#{request_id}",
                    ),
                ]
            ]
        )

        request_text = (
            "📥 <b>New Index Request</b>\n\n"
            f"🎬 <b>File:</b> <code>{file_name}</code>\n"
            f"👤 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
            f"📢 <b>Channel:</b> <code>{file_chat_id}</code>\n"
            f"🆔 <b>Message ID:</b> <code>{file_message_id}</code>"
        )

        if is_admin(message.from_user.id):
            await message.reply_text(
                request_text + "\n\nApprove this file?",
                reply_markup=keyboard,
            )
            return

        # Non-admin requests go to LOG_CHANNEL when configured.
        from info import LOG_CHANNEL

        if not LOG_CHANNEL:
            await message.reply_text(
                "⏳ Request received, but LOG_CHANNEL configure ചെയ്തിട്ടില്ല."
            )
            return

        await client.send_message(
            LOG_CHANNEL,
            request_text,
            reply_markup=keyboard,
        )

        await message.reply_text(
            "✅ Index request അയച്ചു.\n"
            "Admin approve ചെയ്താൽ file database-ൽ add ചെയ്യും."
        )

    except Exception:
        LOGGER.exception("❌ Failed to create manual index request.")
        await message.reply_text(
            "❌ Index request process ചെയ്യുമ്പോൾ error ഉണ്ടായി."
        )


@Client.on_callback_query(filters.regex(r"^index#"))
async def index_callback(client, query):
    """Handle Accept / Reject buttons for manual indexing."""
    if not query.from_user or not is_admin(query.from_user.id):
        await query.answer(
            "❌ Admin only.",
            show_alert=True,
        )
        return

    parts = query.data.split("#", 2)

    if len(parts) != 3:
        await query.answer("❌ Invalid request.", show_alert=True)
        return

    action = parts[1]
    request_id = parts[2]

    request = PENDING_INDEX_REQUESTS.get(request_id)

    if not request:
        await query.answer(
            "⚠️ ഈ request expire ആയിട്ടുണ്ട്.",
            show_alert=True,
        )
        return

    if action == "reject":
        PENDING_INDEX_REQUESTS.pop(request_id, None)

        await query.message.edit_reply_markup(None)

        try:
            await query.message.edit_text(
                (query.message.text or "") + "\n\n❌ <b>Rejected</b>"
            )
        except Exception:
            pass

        await _send_index_result(
            client,
            request["requester_id"],
            "❌ നിങ്ങളുടെ index request admin reject ചെയ്തു.",
        )

        await query.answer("Rejected.")
        return

    if action != "accept":
        await query.answer("❌ Invalid action.", show_alert=True)
        return

    try:
        ok, status, file_name = await _index_single_target(
            client,
            request["file_chat_id"],
            request["file_message_id"],
        )

        PENDING_INDEX_REQUESTS.pop(request_id, None)

        try:
            await query.message.edit_reply_markup(None)
        except Exception:
            pass

        if ok:
            result_text = (
                "✅ <b>Index Approved</b>\n\n"
                f"🎬 <code>{file_name}</code>\n"
                "📦 MongoDB-യിൽ successfully add ചെയ്തു."
            )
            requester_text = (
                "✅ നിങ്ങളുടെ index request approve ചെയ്തു.\n\n"
                f"🎬 <code>{file_name}</code>\n"
                "📦 Database-ൽ add ചെയ്തു."
            )
        elif status == "duplicate":
            result_text = (
                "ℹ️ <b>Already Indexed</b>\n\n"
                f"🎬 <code>{file_name}</code>\n"
                "ഈ file database-ൽ നേരത്തെ തന്നെ ഉണ്ട്."
            )
            requester_text = (
                "ℹ️ ഈ file database-ൽ നേരത്തെ തന്നെ indexed ആണ്."
            )
        elif status == "unsupported":
            result_text = (
                "❌ <b>Unsupported</b>\n"
                "ഈ message-ൽ supported file ഇല്ല."
            )
            requester_text = "❌ ഈ message-ൽ supported file കണ്ടെത്താനായില്ല."
        else:
            result_text = (
                "❌ <b>Index Failed</b>\n\n"
                f"🎬 <code>{file_name or 'Unknown'}</code>"
            )
            requester_text = "❌ File database-ൽ add ചെയ്യാൻ കഴിഞ്ഞില്ല."

        try:
            await query.message.edit_text(
                (query.message.text or "") + "\n\n" + result_text
            )
        except Exception:
            pass

        await _send_index_result(
            client,
            request["requester_id"],
            requester_text,
        )

        await query.answer(
            "Approved." if ok else "Processed.",
            show_alert=False,
        )

    except Exception:
        LOGGER.exception("❌ Manual indexing approval failed.")
        PENDING_INDEX_REQUESTS.pop(request_id, None)

        try:
            await query.message.edit_reply_markup(None)
        except Exception:
            pass

        await _send_index_result(
            client,
            request["requester_id"],
            "❌ Admin approve ചെയ്തെങ്കിലും file database-ൽ add ചെയ്യാൻ error ഉണ്ടായി.",
        )

        await query.answer(
            "❌ Index failed.",
            show_alert=True,
        )
