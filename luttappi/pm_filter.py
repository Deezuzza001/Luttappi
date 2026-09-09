import time

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database.ia_filterdb import search_files
from database.settings_db import get_settings
from info import MAX_RESULTS, SPELLING_CHECK
from utils import normalize_query, humanbytes


# Temporary search cache
SEARCH_CACHE = {}

RESULTS_PER_PAGE = 8


def make_file_button(file_data):
    file_name = file_data.get("file_name", "Unknown File")
    file_size = humanbytes(file_data.get("file_size", 0))

    return InlineKeyboardButton(
        text=f"{file_size} 🌷 {file_name[:42]}",
        callback_data=(
            f"file_"
            f"{file_data['chat_id']}_"
            f"{file_data['message_id']}"
        )
    )


def build_keyboard(results, page=1):
    total_pages = max(
        1,
        (len(results) + RESULTS_PER_PAGE - 1)
        // RESULTS_PER_PAGE
    )

    start = (page - 1) * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE

    current_results = results[start:end]

    buttons = []

    # Language / Quality buttons
    buttons.append([
        InlineKeyboardButton(
            "LANGUAGES",
            callback_data="filter_languages"
        ),
        InlineKeyboardButton(
            "QUALITY",
            callback_data="filter_quality"
        ),
    ])

    # File buttons
    for file_data in current_results:
        buttons.append([
            make_file_button(file_data)
        ])

    # Pagination
    navigation = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ BACK",
                callback_data=f"page_{page - 1}"
            )
        )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                "NEXT ➜",
                callback_data=f"page_{page + 1}"
            )
        )

    if navigation:
        buttons.append(navigation)

    return InlineKeyboardMarkup(buttons)


def build_result_text(query, page, total_results):
    total_pages = max(
        1,
        (total_results + RESULTS_PER_PAGE - 1)
        // RESULTS_PER_PAGE
    )

    return (
        "👋 **HEY** 👋 🙂 🫶\n\n"
        f"📂 **Query :** `{query}`\n\n"
        f"🗓 **Page No ›** `{page}`\n\n"
        "✍️ **NOTE :** ⚠️ This Message\n"
        "Will Be Auto Deleted Within 15 Mins ❗\n"
    )


@Client.on_message(
    filters.private
    & filters.text
    & ~filters.command("start")
)
async def pm_filter(
    client: Client,
    message: Message
):

    if not message.from_user:
        return

    query = normalize_query(message.text)

    if not query:
        return

    settings = await get_settings(
        message.from_user.id
    )

    if not settings.get(
        "auto_filter",
        True
    ):
        return

    results = await search_files(
        query,
        100
    )

    if not results:

        if settings.get(
            "spell_check",
            True
        ):
            await message.reply_text(
                SPELLING_CHECK
            )

        return

    # Save search result
    SEARCH_CACHE[message.from_user.id] = {
        "query": query,
        "results": results,
        "time": time.time(),
    }

    text = build_result_text(
        query,
        1,
        len(results)
    )

    keyboard = build_keyboard(
        results,
        1
    )

    await message.reply_text(
        text,
        reply_markup=keyboard
    )
