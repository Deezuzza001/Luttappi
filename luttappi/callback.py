import time

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.ia_filterdb import get_file
from utils import humanbytes

from plugins.pm_filter import (
    SEARCH_CACHE,
    RESULTS_PER_PAGE,
    build_keyboard,
    build_result_text,
)


def get_user_cache(user_id):
    data = SEARCH_CACHE.get(user_id)

    if not data:
        return None

    # Cache 15 minutes മാത്രം
    if time.time() - data.get("time", 0) > 900:
        SEARCH_CACHE.pop(user_id, None)
        return None

    return data


# =========================
# FILE BUTTON
# =========================

@Client.on_callback_query(
    filters.regex(r"^file_")
)
async def file_callback(
    client: Client,
    query: CallbackQuery
):

    try:
        data = query.data.split("_")

        if len(data) != 3:
            await query.answer(
                "❌ Invalid file request.",
                show_alert=True
            )
            return

        chat_id = int(data[1])
        message_id = int(data[2])

        file_data = await get_file(
            chat_id,
            message_id
        )

        if not file_data:
            await query.answer(
                "❌ File കണ്ടെത്താനായില്ല.",
                show_alert=True
            )
            return

        await query.answer(
            "📤 File അയക്കുന്നു..."
        )

        await client.copy_message(
            chat_id=query.from_user.id,
            from_chat_id=chat_id,
            message_id=message_id
        )

    except Exception as error:

        print(
            f"File callback error: {error}"
        )

        await query.answer(
            "❌ File അയക്കാൻ കഴിഞ്ഞില്ല.",
            show_alert=True
        )


# =========================
# PAGINATION
# =========================

@Client.on_callback_query(
    filters.regex(r"^page_\d+$")
)
async def page_callback(
    client: Client,
    query: CallbackQuery
):

    try:
        page = int(
            query.data.split("_")[1]
        )

        cache = get_user_cache(
            query.from_user.id
        )

        if not cache:
            await query.answer(
                "⚠️ Search expired. വീണ്ടും movie name അയക്കൂ.",
                show_alert=True
            )
            return

        results = cache["results"]
        movie_query = cache["query"]

        total_pages = max(
            1,
            (
                len(results)
                + RESULTS_PER_PAGE
                - 1
            ) // RESULTS_PER_PAGE
        )

        if page < 1 or page > total_pages:
            await query.answer(
                "❌ Invalid page.",
                show_alert=True
            )
            return

        text = build_result_text(
            movie_query,
            page,
            len(results)
        )

        keyboard = build_keyboard(
            results,
            page
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard
        )

        await query.answer()

    except Exception as error:

        print(
            f"Pagination error: {error}"
        )

        await query.answer(
            "❌ Page load failed.",
            show_alert=True
        )


# =========================
# LANGUAGES
# =========================

@Client.on_callback_query(
    filters.regex(r"^filter_languages$")
)
async def language_callback(
    client: Client,
    query: CallbackQuery
):

    buttons = [
        [
            InlineKeyboardButton(
                "🇮🇳 Malayalam",
                callback_data="lang_malayalam"
            ),
            InlineKeyboardButton(
                "🇬🇧 English",
                callback_data="lang_english"
            ),
        ],
        [
            InlineKeyboardButton(
                "🇮🇳 Tamil",
                callback_data="lang_tamil"
            ),
            InlineKeyboardButton(
                "🇮🇳 Telugu",
                callback_data="lang_telugu"
            ),
        ],
        [
            InlineKeyboardButton(
                "🇮🇳 Hindi",
                callback_data="lang_hindi"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="filter_back"
            )
        ]
    ]

    await query.message.edit_reply_markup(
        InlineKeyboardMarkup(buttons)
    )

    await query.answer()


# =========================
# QUALITY
# =========================

@Client.on_callback_query(
    filters.regex(r"^filter_quality$")
)
async def quality_callback(
    client: Client,
    query: CallbackQuery
):

    buttons = [
        [
            InlineKeyboardButton(
                "480p",
                callback_data="quality_480"
            ),
            InlineKeyboardButton(
                "720p",
                callback_data="quality_720"
            ),
        ],
        [
            InlineKeyboardButton(
                "1080p",
                callback_data="quality_1080"
            ),
            InlineKeyboardButton(
                "2160p / 4K",
                callback_data="quality_2160"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="filter_back"
            )
        ]
    ]

    await query.message.edit_reply_markup(
        InlineKeyboardMarkup(buttons)
    )

    await query.answer()


# =========================
# FILTER BACK
# =========================

@Client.on_callback_query(
    filters.regex(r"^filter_back$")
)
async def filter_back_callback(
    client: Client,
    query: CallbackQuery
):

    cache = get_user_cache(
        query.from_user.id
    )

    if not cache:
        await query.answer(
            "⚠️ Search expired.",
            show_alert=True
        )
        return

    keyboard = build_keyboard(
        cache["results"],
        1
    )

    await query.message.edit_reply_markup(
        keyboard
    )

    await query.answer()


# =========================
# LANGUAGE FILTER
# =========================

@Client.on_callback_query(
    filters.regex(r"^lang_")
)
async def language_filter(
    client: Client,
    query: CallbackQuery
):

    language = query.data.replace(
        "lang_",
        ""
    )

    cache = get_user_cache(
        query.from_user.id
    )

    if not cache:
        await query.answer(
            "⚠️ Search expired.",
            show_alert=True
        )
        return

    results = [
        file for file in cache["results"]
        if language.lower()
        in (
            file.get("file_name", "")
            + " "
            + file.get("caption", "")
        ).lower()
    ]

    if not results:
        await query.answer(
            f"❌ {language.title()} files ഇല്ല.",
            show_alert=True
        )
        return

    cache["filtered_results"] = results

    await query.message.edit_text(
        build_result_text(
            cache["query"],
            1,
            len(results)
        ),
        reply_markup=build_keyboard(
            results,
            1
        )
    )

    await query.answer(
        f"🇮🇳 {language.title()} selected"
    )


# =========================
# QUALITY FILTER
# =========================

@Client.on_callback_query(
    filters.regex(r"^quality_")
)
async def quality_filter(
    client: Client,
    query: CallbackQuery
):

    quality = query.data.replace(
        "quality_",
        ""
    )

    quality_map = {
        "480": "480p",
        "720": "720p",
        "1080": "1080p",
        "2160": "2160p",
    }

    quality_text = quality_map.get(
        quality,
        quality
    )

    cache = get_user_cache(
        query.from_user.id
    )

    if not cache:
        await query.answer(
            "⚠️ Search expired.",
            show_alert=True
        )
        return

    results = [
        file for file in cache["results"]
        if quality_text.lower()
        in (
            file.get("file_name", "")
            + " "
            + file.get("caption", "")
        ).lower()
    ]

    if not results:
        await query.answer(
            f"❌ {quality_text} files ഇല്ല.",
            show_alert=True
        )
        return

    cache["filtered_results"] = results

    await query.message.edit_text(
        build_result_text(
            cache["query"],
            1,
            len(results)
        ),
        reply_markup=build_keyboard(
            results,
            1
        )
    )

    await query.answer(
        f"🎬 {quality_text} selected"
    )
