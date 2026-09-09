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

from luttappi.pm_filter import (
    SEARCH_CACHE,
    RESULTS_PER_PAGE,
    build_keyboard,
    build_result_text,
)


@Client.on_message(
    filters.group
    & filters.text
    & ~filters.command(
        ["start", "help", "settings"]
    )
)
async def group_filter(
    client: Client,
    message: Message
):

    if not message.from_user:
        return

    query = normalize_query(
        message.text
    )

    if not query:
        return

    settings = await get_settings(
        message.chat.id
    )

    # Auto Filter OFF
    if not settings.get(
        "auto_filter",
        True
    ):
        return

    results = await search_files(
        query,
        100
    )

    # No results
    if not results:

        if settings.get(
            "spell_check",
            True
        ):
            await message.reply_text(
                SPELLING_CHECK
            )

        return

    # Store search separately for this group/user
    cache_key = (
        message.chat.id,
        message.from_user.id
    )

    SEARCH_CACHE[cache_key] = {
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
