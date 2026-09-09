from pyrogram import Client, filters
from pyrogram.types import Message

from info import OWNER_ID
from database.users_chats_db import get_all_users, get_all_groups


def is_owner(message: Message) -> bool:
    return bool(
        message.from_user
        and message.from_user.id == OWNER_ID
    )


async def broadcast_to_users(client: Client, message: Message):
    success = 0
    failed = 0

    users = get_all_users()

    async for user in users:
        try:
            await message.copy(chat_id=user["_id"])
            success += 1
        except Exception:
            failed += 1

    return success, failed


async def broadcast_to_groups(client: Client, message: Message):
    success = 0
    failed = 0

    groups = get_all_groups()

    async for group in groups:
        try:
            await message.copy(chat_id=group["_id"])
            success += 1
        except Exception:
            failed += 1

    return success, failed


@Client.on_message(
    filters.command("broadcast_users") & filters.private
)
async def broadcast_users(client: Client, message: Message):

    if not is_owner(message):
        return

    if not message.reply_to_message:
        await message.reply_text(
            "📢 **Broadcast ചെയ്യേണ്ട message-ന് reply ചെയ്ത്:**\n"
            "`/broadcast_users`"
        )
        return

    status = await message.reply_text(
        "📤 **Users Broadcast Started...**"
    )

    success, failed = await broadcast_to_users(
        client,
        message.reply_to_message
    )

    await status.edit_text(
        "✅ **Users Broadcast Completed**\n\n"
        f"👤 Success: `{success}`\n"
        f"❌ Failed: `{failed}`"
    )


@Client.on_message(
    filters.command("broadcast_groups") & filters.private
)
async def broadcast_groups(client: Client, message: Message):

    if not is_owner(message):
        return

    if not message.reply_to_message:
        await message.reply_text(
            "📢 **Broadcast ചെയ്യേണ്ട message-ന് reply ചെയ്ത്:**\n"
            "`/broadcast_groups`"
        )
        return

    status = await message.reply_text(
        "📤 **Groups Broadcast Started...**"
    )

    success, failed = await broadcast_to_groups(
        client,
        message.reply_to_message
    )

    await status.edit_text(
        "✅ **Groups Broadcast Completed**\n\n"
        f"👥 Success: `{success}`\n"
        f"❌ Failed: `{failed}`"
    )
