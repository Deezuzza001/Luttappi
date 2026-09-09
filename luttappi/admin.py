from pyrogram import Client, filters
from pyrogram.types import Message

from info import OWNER_ID
from database.users_chats_db import total_users, total_groups
from database.ia_filterdb import total_files


def is_owner(message: Message) -> bool:
    return bool(
        message.from_user
        and message.from_user.id == OWNER_ID
    )


@Client.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):

    if not is_owner(message):
        return

    users = await total_users()
    groups = await total_groups()
    files = await total_files()

    await message.reply_text(
        "📊 **Bot Statistics**\n\n"
        f"👤 Users: `{users}`\n"
        f"👥 Groups: `{groups}`\n"
        f"📁 Files: `{files}`"
    )


@Client.on_message(filters.command("users") & filters.private)
async def users_command(client: Client, message: Message):

    if not is_owner(message):
        return

    users = await total_users()

    await message.reply_text(
        f"👤 **Total Users:** `{users}`"
    )


@Client.on_message(filters.command("groups") & filters.private)
async def groups_command(client: Client, message: Message):

    if not is_owner(message):
        return

    groups = await total_groups()

    await message.reply_text(
        f"👥 **Total Groups:** `{groups}`"
    )


@Client.on_message(filters.command("files") & filters.private)
async def files_command(client: Client, message: Message):

    if not is_owner(message):
        return

    files = await total_files()

    await message.reply_text(
        f"📁 **Total Indexed Files:** `{files}`"
    )
