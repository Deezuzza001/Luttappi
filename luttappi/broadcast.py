import asyncio

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from info import OWNER_ID
from database.users_chats_db import get_all_users, get_all_groups


def is_owner(message: Message) -> bool:
    return bool(
        message.from_user
        and message.from_user.id == OWNER_ID
    )


async def _copy_with_retry(
    message: Message,
    chat_id: int,
) -> bool:
    """Copy one broadcast message and safely handle Telegram FloodWait."""
    while True:
        try:
            await message.copy(chat_id=chat_id)
            return True
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            return False


async def broadcast_to_users(
    client: Client,
    message: Message,
):
    success = 0
    failed = 0

    users = get_all_users()

    async for user in users:
        if await _copy_with_retry(message, user["_id"]):
            success += 1
        else:
            failed += 1

        # Small delay helps reduce flood-limit errors.
        await asyncio.sleep(0.05)

    return success, failed


async def broadcast_to_groups(
    client: Client,
    message: Message,
):
    success = 0
    failed = 0

    groups = get_all_groups()

    async for group in groups:
        if await _copy_with_retry(message, group["_id"]):
            success += 1
        else:
            failed += 1

        await asyncio.sleep(0.05)

    return success, failed


@Client.on_message(
    filters.command("broadcast_users") & filters.private
)
async def broadcast_users(
    client: Client,
    message: Message,
):
    if not is_owner(message):
        return

    if not message.reply_to_message:
        await message.reply_text(
            "📢 **Broadcast ചെയ്യേണ്ട message-ന് reply ചെയ്ത്:**\n"
            "`/broadcast_users`"
        )
        return

    status = await message.reply_text(
        "📤 **Users Broadcast Started...**\n\n"
        "⏳ Please wait..."
    )

    success, failed = await broadcast_to_users(
        client,
        message.reply_to_message,
    )

    await status.edit_text(
        "✅ **Users Broadcast Completed**\n\n"
        f"👤 Success: `{success}`\n"
        f"❌ Failed: `{failed}`"
    )


@Client.on_message(
    filters.command("broadcast_groups") & filters.private
)
async def broadcast_groups(
    client: Client,
    message: Message,
):
    if not is_owner(message):
        return

    if not message.reply_to_message:
        await message.reply_text(
            "📢 **Broadcast ചെയ്യേണ്ട message-ന് reply ചെയ്ത്:**\n"
            "`/broadcast_groups`"
        )
        return

    status = await message.reply_text(
        "📤 **Groups Broadcast Started...**\n\n"
        "⏳ Please wait..."
    )

    success, failed = await broadcast_to_groups(
        client,
        message.reply_to_message,
    )

    await status.edit_text(
        "✅ **Groups Broadcast Completed**\n\n"
        f"👥 Success: `{success}`\n"
        f"❌ Failed: `{failed}`"
    )
