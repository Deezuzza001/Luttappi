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

        # User must have started the bot in PM
        try:
            await client.get_chat(
                query.from_user.id
            )
        except Exception:
            await query.answer(
                "⚠️ ആദ്യം Bot-ന്റെ PM-ൽ /start ചെയ്യൂ.",
                show_alert=True
            )
            return

        await query.answer(
            "📤 File PM-ലേക്ക് അയക്കുന്നു..."
        )

        await client.copy_message(
            chat_id=query.from_user.id,
            from_chat_id=chat_id,
            message_id=message_id
        )

    except Exception as error:
        print(f"File callback error: {error}")

        await query.answer(
            "❌ File അയക്കാൻ കഴിഞ്ഞില്ല.",
            show_alert=True
        )
