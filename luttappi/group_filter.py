from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from database.ia_filterdb import search_files
from database.settings_db import get_settings
from info import MAX_RESULTS, SPELLING_CHECK
from utils import normalize_query


@Client.on_message(
    filters.group
    & filters.text
    & ~filters.command(["start", "help", "settings"])
)
async def group_filter(client: Client, message: Message):

    query = normalize_query(message.text)

    if not query:
        return

    settings = await get_settings(message.chat.id)

    if not settings.get("auto_filter", True):
        return

    results = await search_files(query, MAX_RESULTS)

    # No result
    if not results:
        if settings.get("spell_check", True):
            await message.reply_text(SPELLING_CHECK)
        return

    buttons = []

    for file in results:
        file_name = file.get("file_name", "File")
        chat_id = file.get("chat_id")
        message_id = file.get("message_id")

        if not chat_id or not message_id:
            continue

        buttons.append([
            InlineKeyboardButton(
                text=file_name[:50],
                callback_data=f"file_{chat_id}_{message_id}"
            )
        ])

    if not buttons:
        return

    await message.reply_text(
        f"🎬 **{query.title()}**\n\n"
        "👇 Available files:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
