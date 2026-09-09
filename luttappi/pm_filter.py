import time

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.ia_filterdb import search_files
from database.settings_db import get_settings
from info import SPELLING_CHECK
from utils import normalize_query, humanbytes


# ---------------------------------------------------------
# SEARCH CACHE
# ---------------------------------------------------------

SEARCH_CACHE = {}

RESULTS_PER_PAGE = 8
CACHE_TIMEOUT = 900  # 15 minutes


# ---------------------------------------------------------
# FILE BUTTON
# ---------------------------------------------------------

def make_file_button(file_data):
    file_name = file_data.get("file_name", "Unknown File")
    file_size = humanbytes(file_data.get("file_size", 0))

    chat_id = file_data.get("chat_id")
    message_id = file_data.get("message_id")

    return InlineKeyboardButton(
        text=f"{file_size} 🌷 {file_name[:42]}",
        callback_data=f"file_{chat_id}_{message_id}"
    )


# ---------------------------------------------------------
# RESULT KEYBOARD
# ---------------------------------------------------------

def build_keyboard(results, page=1, show_filter_buttons=True):
    if not results:
        return None

    total_pages = max(
        1,
        (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    )

    page = max(1, min(page, total_pages))

    start = (page - 1) * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE

    current_results = results[start:end]

    buttons = []

    # Filter buttons
    if show_filter_buttons:
        buttons.append([
            InlineKeyboardButton(
                "LANGUAGES",
                callback_data="filter_languages"
            ),
            InlineKeyboardButton(
                "QUALITY",
                callback_data="filter_quality"
            )
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


# ---------------------------------------------------------
# RESULT TEXT
# ---------------------------------------------------------

def build_result_text(query, page, total_results, user_name):
    total_pages = max(
        1,
        (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    )

    return (
        f"👋 **HEY {user_name}** 🫶\n\n"
        f"📂 **Query :** `{query}`\n\n"
        f"🗓 **Page No ›** `{page}` / `{total_pages}`\n\n"
        f"🎬 **Results :** `{total_results}`\n\n"
        "✍️ **NOTE :** ⚠️ Search buttons will "
        "expire after 15 minutes ❗"
    )


# ---------------------------------------------------------
# CACHE CLEANUP
# ---------------------------------------------------------

def save_search_cache(cache_key, query, results):
    SEARCH_CACHE[cache_key] = {
        "query": query,
        "results": results,
        "time": time.time(),
    }


def get_search_cache(cache_key):
    data = SEARCH_CACHE.get(cache_key)

    if not data:
        return None

    # Remove expired cache
    if time.time() - data["time"] > CACHE_TIMEOUT:
        SEARCH_CACHE.pop(cache_key, None)
        return None

    return data


# ---------------------------------------------------------
# PRIVATE MESSAGE AUTO FILTER
# ---------------------------------------------------------

@Client.on_message(
    filters.private
    & filters.text
    & ~filters.command("start")
)
async def pm_filter(client, message):

    if not message.from_user:
        return

    # Clean / normalize movie query
    query = normalize_query(message.text)

    if not query:
        return

    # User settings
    settings = await get_settings(message.from_user.id)

    if not settings.get("auto_filter", True):
        return

    # Search database
    # Keep the internal result pool larger than one page so that
    # pagination can actually show additional pages.
    results = await search_files(
        query,
        100
    )

    # -----------------------------------------------------
    # NO RESULT
    # -----------------------------------------------------

    if not results:

        if settings.get("spell_check", True):
            await message.reply_text(
                SPELLING_CHECK
            )

        return

    # -----------------------------------------------------
    # SAVE SEARCH CACHE
    # -----------------------------------------------------

    cache_key = message.from_user.id

    save_search_cache(
        cache_key,
        query,
        results
    )

    # -----------------------------------------------------
    # RESULT MESSAGE
    # -----------------------------------------------------

    user_name = message.from_user.first_name or "User"

    text = build_result_text(
        query,
        1,
        len(results),
        user_name
    )

    keyboard = build_keyboard(
        results,
        1,
        show_filter_buttons=settings.get("suggestions", True)
    )

    await message.reply_text(
        text,
        reply_markup=keyboard
    )
