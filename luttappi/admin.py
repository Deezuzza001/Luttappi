from pyrogram import Client, filters

from database.users_chats_db import (
    total_users,
    total_groups,
)
from database.ia_filterdb import total_files
from info import OWNER_ID


# ---------------------------------------------------------
# OWNER CHECK
# ---------------------------------------------------------

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# ---------------------------------------------------------
# STATS
# ---------------------------------------------------------

@Client.on_message(
    filters.command("stats") & filters.private
)
async def stats_command(client, message):

    if not message.from_user or not is_owner(
        message.from_user.id
    ):
        return

    users = await total_users()
    groups = await total_groups()
    files = await total_files()

    await message.reply_text(
        "📊 **BOT STATISTICS**\n\n"
        f"👤 **Users:** `{users}`\n"
        f"👥 **Groups:** `{groups}`\n"
        f"📁 **Files:** `{files}`"
    )


# ---------------------------------------------------------
# USERS
# ---------------------------------------------------------

@Client.on_message(
    filters.command("users") & filters.private
)
async def users_command(client, message):

    if not message.from_user or not is_owner(
        message.from_user.id
    ):
        return

    users = await total_users()

    await message.reply_text(
        "👤 **USER STATISTICS**\n\n"
        f"Total Users: `{users}`"
    )


# ---------------------------------------------------------
# GROUPS
# ---------------------------------------------------------

@Client.on_message(
    filters.command("groups") & filters.private
)
async def groups_command(client, message):

    if not message.from_user or not is_owner(
        message.from_user.id
    ):
        return

    groups = await total_groups()

    await message.reply_text(
        "👥 **GROUP STATISTICS**\n\n"
        f"Total Groups: `{groups}`"
    )


# ---------------------------------------------------------
# FILES
# ---------------------------------------------------------

@Client.on_message(
    filters.command("files") & filters.private
)
async def files_command(client, message):

    if not message.from_user or not is_owner(
        message.from_user.id
    ):
        return

    files = await total_files()

    await message.reply_text(
        "📁 **FILE DATABASE**\n\n"
        f"Total Files: `{files}`"
    )
