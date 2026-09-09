from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from database.users_chats_db import save_user, save_group
from info import START_PIC, FORCE_SUB_CHANNEL, UPDATE_CHANNEL


def channel_link(value):
    if not value:
        return None
    value = str(value).strip()
    if value.startswith("https://") or value.startswith("http://"):
        return value
    if value.startswith("@"):
        return f"https://t.me/{value[1:]}"
    return f"https://t.me/{value}"


async def is_subscribed(client: Client, user_id: int) -> bool:
    if not FORCE_SUB_CHANNEL:
        return True

    try:
        member = await client.get_chat_member(
            int(FORCE_SUB_CHANNEL),
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

    update_link = channel_link(UPDATE_CHANNEL)
    if update_link:
        buttons.append([
            InlineKeyboardButton("📢 UPDATE CHANNEL", url=update_link)
        ])

    if FORCE_SUB_CHANNEL:
        join_link = channel_link(UPDATE_CHANNEL)
        if join_link:
            buttons.append([
                InlineKeyboardButton("📢 JOIN CHANNEL", url=join_link)
            ])

        buttons.append([
            InlineKeyboardButton(
                "✅ I HAVE JOINED",
                callback_data="check_subscription",
            )
        ])

    buttons.append([
        InlineKeyboardButton("ℹ️ ABOUT", callback_data="start_about"),
        InlineKeyboardButton("❌ CLOSE", callback_data="start_close"),
    ])

    return InlineKeyboardMarkup(buttons)


START_TEXT = (
    "👋 **Hello {name}!**\n\n"
    "🎬 **Advanced Auto Filter Bot**-ലേക്ക് സ്വാഗതം!\n\n"
    "🔎 Movie name അയക്കൂ, available files ഞാൻ കണ്ടെത്തിത്തരാം.\n\n"
    "⚡ Fast • Smart • Auto Filter"
)


async def send_start_message(client: Client, message: Message):
    user = message.from_user
    name = user.first_name if user else "User"

    if FORCE_SUB_CHANNEL and user:
        if not await is_subscribed(client, user.id):
            join_link = channel_link(UPDATE_CHANNEL)

            buttons = []
            if join_link:
                buttons.append([
                    InlineKeyboardButton("📢 JOIN CHANNEL", url=join_link)
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

            text = (
                f"👋 **Hello {name}!**\n\n"
                "🔒 **Bot ഉപയോഗിക്കാൻ ആദ്യം നമ്മുടെ channel join ചെയ്യുക.**\n\n"
                "Join ചെയ്ത ശേഷം **I HAVE JOINED** അമർത്തുക."
            )

            if START_PIC:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=START_PIC,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            return

    keyboard = start_keyboard()

    if START_PIC:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=START_PIC,
            caption=START_TEXT.format(name=name),
            reply_markup=keyboard,
        )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text=START_TEXT.format(name=name),
            reply_markup=keyboard,
        )


@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    if message.from_user:
        await save_user(message.from_user)

    await send_start_message(client, message)


@Client.on_message(filters.group)
async def save_group_data(client: Client, message: Message):
    if message.chat:
        await save_group(message.chat)
