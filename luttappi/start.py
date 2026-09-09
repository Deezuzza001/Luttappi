from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.enums import ChatMemberStatus

from database.users_chats_db import save_user, save_group
from info import (
    FORCE_SUB_CHANNEL,
    UPDATE_CHANNEL,
    BOT_USERNAME,
    START_PIC,
)


def get_update_url():
    if not UPDATE_CHANNEL:
        return None

    channel = UPDATE_CHANNEL.strip()

    if channel.startswith("https://t.me/"):
        return channel

    if channel.startswith("@"):
        channel = channel[1:]

    return f"https://t.me/{channel}"


def get_force_channel_id():
    if not FORCE_SUB_CHANNEL:
        return None

    try:
        return int(str(FORCE_SUB_CHANNEL).strip())
    except (TypeError, ValueError):
        return None


async def is_subscribed(client, user_id):
    channel_id = get_force_channel_id()

    if not channel_id:
        return True

    try:
        member = await client.get_chat_member(
            channel_id,
            user_id,
        )

        return member.status in (
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        )

    except Exception:
        return False


def start_keyboard():
    buttons = []

    update_url = get_update_url()

    if update_url:
        buttons.append([
            InlineKeyboardButton(
                "📢 UPDATE CHANNEL",
                url=update_url,
            )
        ])

    if FORCE_SUB_CHANNEL:
        update_url = get_update_url()

        if update_url:
            buttons.append([
                InlineKeyboardButton(
                    "🔒 JOIN CHANNEL",
                    url=update_url,
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "✅ I HAVE JOINED",
                callback_data="check_subscription",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "ℹ️ ABOUT",
            callback_data="start_about",
        ),
        InlineKeyboardButton(
            "❌ CLOSE",
            callback_data="start_close",
        ),
    ])

    return InlineKeyboardMarkup(buttons)


def about_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 BACK",
                callback_data="start_back",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ CLOSE",
                callback_data="start_close",
            ),
        ],
    ])


async def send_start_message(client, message):
    user = message.from_user

    start_text = (
        f"👋 **HEY {user.first_name}** 🫶\n\n"
        "🎬 **Advanced Auto Filter Bot**-ലേക്ക് സ്വാഗതം!\n\n"
        "🔎 Movie name അയക്കൂ, available files ഞാൻ "
        "കണ്ടെത്തിത്തരാം.\n\n"
        "⚡ Fast • Smart • Auto Filter"
    )

    keyboard = start_keyboard()

    if START_PIC:
        await message.reply_photo(
            photo=START_PIC,
            caption=start_text,
            reply_markup=keyboard,
        )
    else:
        await message.reply_text(
            start_text,
            reply_markup=keyboard,
        )


@Client.on_message(
    filters.command("start") & filters.private
)
async def start_command(
    client: Client,
    message: Message,
):
    await save_user(message.from_user)

    if not await is_subscribed(
        client,
        message.from_user.id,
    ):
        join_text = (
            "🔒 **CHANNEL JOIN REQUIRED**\n\n"
            "Bot ഉപയോഗിക്കുന്നതിന് മുമ്പ് ഞങ്ങളുടെ "
            "channel join ചെയ്യുക.\n\n"
            "Join ചെയ്ത ശേഷം **I HAVE JOINED** അമർത്തുക."
        )

        await message.reply_text(
            join_text,
            reply_markup=start_keyboard(),
        )
        return

    await send_start_message(
        client,
        message,
    )


@Client.on_message(filters.group)
async def save_group_data(
    client: Client,
    message: Message,
):
    await save_group(message.chat)
