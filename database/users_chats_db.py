from database import users, groups


# =========================
# User Management
# =========================

async def save_user(user):
    """Save or update a Telegram user."""

    if not user:
        return

    await users.update_one(
        {"_id": user.id},
        {
            "$set": {
                "user_id": user.id,
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "username": user.username or "",
            }
        },
        upsert=True,
    )


async def is_user_exist(user_id: int):
    """Check whether a user exists."""

    return await users.find_one(
        {"_id": user_id}
    ) is not None


async def get_user(user_id: int):
    """Get user information."""

    return await users.find_one(
        {"_id": user_id}
    )


async def delete_user(user_id: int):
    """Delete a user."""

    await users.delete_one(
        {"_id": user_id}
    )


async def get_all_users():
    """Return all users."""

    return users.find({})


async def total_users():
    """Return total user count."""

    return await users.count_documents({})


# =========================
# Group Management
# =========================

async def save_group(chat):
    """Save or update a Telegram group."""

    if not chat:
        return

    await groups.update_one(
        {"_id": chat.id},
        {
            "$set": {
                "chat_id": chat.id,
                "title": chat.title or "",
                "username": chat.username or "",
            }
        },
        upsert=True,
    )


async def is_group_exist(chat_id: int):
    """Check whether a group exists."""

    return await groups.find_one(
        {"_id": chat_id}
    ) is not None


async def get_group(chat_id: int):
    """Get group information."""

    return await groups.find_one(
        {"_id": chat_id}
    )


async def delete_group(chat_id: int):
    """Delete a group."""

    await groups.delete_one(
        {"_id": chat_id}
    )


async def get_all_groups():
    """Return all groups."""

    return groups.find({})


async def total_groups():
    """Return total group count."""

    return await groups.count_documents({})
