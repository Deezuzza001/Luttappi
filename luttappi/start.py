from pyrogram import Client, filters
from pyrogram.types import Message

from database.users_chats_db import save_user, save_group


@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    await save_user(message.from_user)

    await message.reply_text(
        f"👋 Hello {message.from_user.mention}!\n\n"
        "🎬 **Advanced Auto Filter Bot**-ലേക്ക് സ്വാഗതം!\n\n"
        "🔎 Movie name അയക്കൂ, available files ഞാൻ കണ്ടെത്തിത്തരാം.\n\n"
        "⚡ Fast • Smart • Auto Filter"
    )


@Client.on_message(filters.group)
async def save_group_data(client: Client, message: Message):
    await save_group(message.chat)
