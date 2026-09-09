from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from database.settings_db import get_settings, update_setting


def settings_keyboard(settings):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"🔎 Auto Filter: {'ON' if settings.get('auto_filter') else 'OFF'}",
                callback_data="set_auto_filter"
            )
        ],
        [
            InlineKeyboardButton(
                f"✍️ Spelling Check: {'ON' if settings.get('spell_check') else 'OFF'}",
                callback_data="set_spell_check"
            )
        ],
        [
            InlineKeyboardButton(
                f"🎬 Suggestions: {'ON' if settings.get('suggestions') else 'OFF'}",
                callback_data="set_suggestions"
            )
        ],
        [
            InlineKeyboardButton(
                f"🗑 Auto Delete: {'ON' if settings.get('auto_delete') else 'OFF'}",
                callback_data="set_auto_delete"
            )
        ],
    ])


@Client.on_message(
    filters.command("settings") & filters.group
)
async def settings_command(client: Client, message: Message):

    member = await client.get_chat_member(
        message.chat.id,
        message.from_user.id
    )

    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        await message.reply_text(
            "❌ ഈ command ഉപയോഗിക്കാൻ Group Admin ആയിരിക്കണം."
        )
        return

    settings = await get_settings(message.chat.id)

    await message.reply_text(
        "⚙️ **Group Settings**\n\n"
        "താഴെയുള്ള buttons ഉപയോഗിച്ച് settings മാറ്റാം.",
        reply_markup=settings_keyboard(settings)
    )


@Client.on_callback_query(filters.regex(r"^set_"))
async def settings_callback(
    client: Client,
    query: CallbackQuery
):

    message = query.message

    if not message or message.chat.type.value not in ("group", "supergroup"):
        await query.answer("❌ Group settings മാത്രം.", show_alert=True)
        return

    member = await client.get_chat_member(
        message.chat.id,
        query.from_user.id
    )

    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        await query.answer(
            "❌ Admin മാത്രം settings മാറ്റാം.",
            show_alert=True
        )
        return

    key = query.data.replace("set_", "")

    allowed_keys = {
        "auto_filter",
        "spell_check",
        "suggestions",
        "auto_delete",
    }

    if key not in allowed_keys:
        await query.answer("❌ Invalid setting.", show_alert=True)
        return

    settings = await get_settings(message.chat.id)

    current = settings.get(key, False)
    new_value = not current

    await update_setting(
        message.chat.id,
        key,
        new_value
    )

    settings[key] = new_value

    await query.message.edit_reply_markup(
        reply_markup=settings_keyboard(settings)
    )

    await query.answer(
        f"{key.replace('_', ' ').title()}: "
        f"{'ON' if new_value else 'OFF'}"
    )
