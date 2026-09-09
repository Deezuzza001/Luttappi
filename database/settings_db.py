from database import settings


# =========================
# Default Settings
# =========================

DEFAULT_SETTINGS = {
    "auto_filter": True,
    "spell_check": True,
    "suggestions": True,
    "auto_delete": True,
    "delete_time": 300,
}


# =========================
# Get Group Settings
# =========================

async def get_settings(chat_id: int):
    """Get settings for a group."""

    data = await settings.find_one(
        {"_id": chat_id}
    )

    if data:
        return data

    default_data = {
        "_id": chat_id,
        **DEFAULT_SETTINGS
    }

    await settings.insert_one(
        default_data
    )

    return default_data


# =========================
# Update Setting
# =========================

async def update_setting(
    chat_id: int,
    key: str,
    value
):
    """Update one group setting."""

    await settings.update_one(
        {"_id": chat_id},
        {
            "$set": {
                key: value
            }
        },
        upsert=True
    )

    return True


# =========================
# Get Single Setting
# =========================

async def get_setting(
    chat_id: int,
    key: str,
    default=None
):
    """Get a single setting."""

    data = await settings.find_one(
        {"_id": chat_id}
    )

    if not data:
        return default

    return data.get(
        key,
        default
    )


# =========================
# Delete Group Settings
# =========================

async def delete_settings(
    chat_id: int
):
    """Delete all settings for a group."""

    result = await settings.delete_one(
        {"_id": chat_id}
    )

    return result.deleted_count > 0
