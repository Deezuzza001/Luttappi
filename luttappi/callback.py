import time

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database.ia_filterdb import get_file
from luttappi.pm_filter import (
    SEARCH_CACHE,
    RESULTS_PER_PAGE,
    build_keyboard,
    build_result_text,
)

CACHE_TIMEOUT = 900  # 15 minutes


def get_cache_key(query: CallbackQuery):
    """Use the same cache key for PM and Group searches."""
    message = query.message

    if message and message.chat:
        chat_type = message.chat.type.value

        if chat_type in ("group", "supergroup"):
            return (message.chat.id, query.from_user.id)

    return query.from_user.id


def get_user_cache(query: CallbackQuery):
    key = get_cache_key(query)
    data = SEARCH_CACHE.get(key)

    if not data:
        return None

    if time.time() - data.get("time", 0) > CACHE_TIMEOUT:
        SEARCH_CACHE.pop(key, None)
        return None

    return data


async def restore_page(query: CallbackQuery, results, page: int, movie_query: str):
    total_pages = max(
        1,
        (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    )

    if page < 1 or page > total_pages:
        await query.answer("❌ Invalid page.", show_alert=True)
        return

    await query.message.edit_text(
        build_result_text(movie_query, page, len(results)),
        reply_markup=build_keyboard(results, page),
    )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^file_"))
async def file_callback(client: Client, query: CallbackQuery):
    try:
        parts = query.data.split("_")

        if len(parts) != 3:
            await query.answer(
                "❌ Invalid file request.",
                show_alert=True,
            )
            return

        chat_id = int(parts[1])
        message_id = int(parts[2])

        file_data = await get_file(chat_id, message_id)

        if not file_data:
            await query.answer(
                "❌ File കണ്ടെത്താനായില്ല.",
                show_alert=True,
            )
            return

        await query.answer("📤 File PM-ലേക്ക് അയക്കുന്നു...")

        try:
            await client.copy_message(
                chat_id=query.from_user.id,
                from_chat_id=chat_id,
                message_id=message_id,
            )
        except Exception:
            await query.answer(
                "⚠️ ആദ്യം Bot-ന്റെ PM-ൽ /start ചെയ്യൂ.",
                show_alert=True,
            )

    except Exception as error:
        print(f"File callback error: {error}")
        try:
            await query.answer(
                "❌ File അയക്കാൻ കഴിഞ്ഞില്ല.",
                show_alert=True,
            )
        except Exception:
            pass


@Client.on_callback_query(filters.regex(r"^page_\d+$"))
async def page_callback(client: Client, query: CallbackQuery):
    try:
        page = int(query.data.split("_")[1])
        cache = get_user_cache(query)

        if not cache:
            await query.answer(
                "⚠️ Search expired. വീണ്ടും movie name അയക്കൂ.",
                show_alert=True,
            )
            return

        results = cache.get("filtered_results") or cache["results"]

        await restore_page(
            query,
            results,
            page,
            cache["query"],
        )

    except Exception as error:
        print(f"Pagination error: {error}")
        await query.answer(
            "❌ Page load failed.",
            show_alert=True,
        )


@Client.on_callback_query(filters.regex(r"^filter_languages$"))
async def language_menu(client: Client, query: CallbackQuery):
    buttons = [
        [
            InlineKeyboardButton(
                "🇮🇳 Malayalam",
                callback_data="lang_malayalam",
            ),
            InlineKeyboardButton(
                "🇬🇧 English",
                callback_data="lang_english",
            ),
        ],
        [
            InlineKeyboardButton(
                "🇮🇳 Tamil",
                callback_data="lang_tamil",
            ),
            InlineKeyboardButton(
                "🇮🇳 Telugu",
                callback_data="lang_telugu",
            ),
        ],
        [
            InlineKeyboardButton(
                "🇮🇳 Hindi",
                callback_data="lang_hindi",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="filter_back",
            ),
        ],
    ]

    await query.message.edit_reply_markup(
        InlineKeyboardMarkup(buttons)
    )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^filter_quality$"))
async def quality_menu(client: Client, query: CallbackQuery):
    buttons = [
        [
            InlineKeyboardButton(
                "480p",
                callback_data="quality_480",
            ),
            InlineKeyboardButton(
                "720p",
                callback_data="quality_720",
            ),
        ],
        [
            InlineKeyboardButton(
                "1080p",
                callback_data="quality_1080",
            ),
            InlineKeyboardButton(
                "2160p / 4K",
                callback_data="quality_2160",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="filter_back",
            ),
        ],
    ]

    await query.message.edit_reply_markup(
        InlineKeyboardMarkup(buttons)
    )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^filter_back$"))
async def filter_back(client: Client, query: CallbackQuery):
    cache = get_user_cache(query)

    if not cache:
        await query.answer(
            "⚠️ Search expired. വീണ്ടും movie name അയക്കൂ.",
            show_alert=True,
        )
        return

    cache.pop("filtered_results", None)

    await query.message.edit_reply_markup(
        build_keyboard(cache["results"], 1)
    )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^lang_"))
async def language_filter(client: Client, query: CallbackQuery):
    language = query.data.replace("lang_", "")
    cache = get_user_cache(query)

    if not cache:
        await query.answer(
            "⚠️ Search expired. വീണ്ടും movie name അയക്കൂ.",
            show_alert=True,
        )
        return

    searchable = {
        "malayalam": ["malayalam", "mal"],
        "english": ["english", "eng"],
        "tamil": ["tamil"],
        "telugu": ["telugu"],
        "hindi": ["hindi"],
    }

    keywords = searchable.get(language, [language])

    results = [
        file
        for file in cache["results"]
        if any(
            keyword in (
                file.get("file_name", "")
                + " "
                + file.get("caption", "")
            ).lower()
            for keyword in keywords
        )
    ]

    if not results:
        await query.answer(
            f"❌ {language.title()} files ഇല്ല.",
            show_alert=True,
        )
        return

    cache["filtered_results"] = results

    await query.message.edit_text(
        build_result_text(
            cache["query"],
            1,
            len(results),
        ),
        reply_markup=build_keyboard(results, 1),
    )

    await query.answer(
        f"🌐 {language.title()} selected"
    )


@Client.on_callback_query(filters.regex(r"^quality_"))
async def quality_filter(client: Client, query: CallbackQuery):
    quality = query.data.replace("quality_", "")

    quality_map = {
        "480": ["480p", "480"],
        "720": ["720p", "720"],
        "1080": ["1080p", "1080"],
        "2160": ["2160p", "2160", "4k"],
    }

    keywords = quality_map.get(quality, [quality])
    cache = get_user_cache(query)

    if not cache:
        await query.answer(
            "⚠️ Search expired. വീണ്ടും movie name അയക്കൂ.",
            show_alert=True,
        )
        return

    results = [
        file
        for file in cache["results"]
        if any(
            keyword in (
                file.get("file_name", "")
                + " "
                + file.get("caption", "")
            ).lower()
            for keyword in keywords
        )
    ]

    quality_text = "4K" if quality == "2160" else f"{quality}p"

    if not results:
        await query.answer(
            f"❌ {quality_text} files ഇല്ല.",
            show_alert=True,
        )
        return

    cache["filtered_results"] = results

    await query.message.edit_text(
        build_result_text(
            cache["query"],
            1,
            len(results),
        ),
        reply_markup=build_keyboard(results, 1),
    )

    await query.answer(
        f"🎬 {quality_text} selected"
    )

