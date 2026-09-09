from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from database.ia_filterdb import get_file


@Client.on_callback_query(filters.regex(r"^file_"))
async def file_callback(client: Client, query: CallbackQuery):
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

        file_data = await get_file(chat_id, message_id)

        if not file_data:
            await query.answer(
                "❌ File കണ്ടെത്താനായില്ല.",
                show_alert=True
            )
            return

        await query.answer("📤 File അയക്കുന്നു...")

        await client.copy_message(
            chat_id=query.from_user.id,
            from_chat_id=chat_id,
            message_id=message_id
        )

    except Exception as e:
        await query.answer(
            "❌ File അയക്കാൻ കഴിഞ്ഞില്ല.",
            show_alert=True
        )
        print(f"File callback error: {e}")
