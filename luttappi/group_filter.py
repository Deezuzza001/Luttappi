import time

from pyrogram import Client, filters

from database.ia_filterdb import search_files
from database.settings_db import get_settings
from info import MAX_RESULTS, SPELLING_CHECK
from utils import normalize_query

from luttappi.pm_filter import (
    SEARCH_CACHE,
    build_keyboard,
    build_result_text,
    save_search_cache,
)


@Client.on_message(
    filters.group
    & filters.text
    & ~filters.command(["start", "help", "settings"])
)
async def group_filter(client, message):

    if not message.from_user:
        return

    # Normalize movie name
    query = normalize_query(message.text)

    if not query:
        return

    # Group settings
    settings = await get_settings(message.chat.id)

    if not settings.get("auto_filter", True):
        return

    # Search database
    results = await search_files(
        query,
        MAX_RESULTS
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
    # GROUP CACHE
    # -----------------------------------------------------

    cache_key = (
        message.chat.id,
        message.from_user.id
    )

    save_search_cache(
        cache_key,
        query,
        results
    )

    # -----------------------------------------------------
    # RESULT MESSAGE
    # -----------------------------------------------------

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
