from database import files


# =========================
# Database Indexes
# =========================

async def create_indexes():
    """Create MongoDB indexes for faster searching."""

    await files.create_index(
        [
            ("chat_id", 1),
            ("message_id", 1)
        ],
        unique=True,
        name="unique_file_message"
    )

    await files.create_index(
        [("file_name", "text")],
        name="file_name_text"
    )


# =========================
# Save File
# =========================

async def save_file(file_data: dict):
    """Save or update a Telegram file."""

    if not file_data:
        return False

    chat_id = file_data.get("chat_id")
    message_id = file_data.get("message_id")

    if not chat_id or not message_id:
        return False

    await files.update_one(
        {
            "chat_id": chat_id,
            "message_id": message_id
        },
        {
            "$set": file_data
        },
        upsert=True
    )

    return True


# =========================
# Search Files
# =========================

async def search_files(
    query: str,
    limit: int = 10
):
    """Search movie/file names."""

    if not query:
        return []

    query = query.strip()

    cursor = files.find(
        {
            "$or": [
                {
                    "file_name": {
                        "$regex": query,
                        "$options": "i"
                    }
                },
                {
                    "caption": {
                        "$regex": query,
                        "$options": "i"
                    }
                }
            ]
        }
    ).limit(limit)

    return await cursor.to_list(
        length=limit
    )


# =========================
# Get File
# =========================

async def get_file(
    chat_id: int,
    message_id: int
):
    """Get a single indexed file."""

    return await files.find_one(
        {
            "chat_id": chat_id,
            "message_id": message_id
        }
    )


# =========================
# Delete File
# =========================

async def delete_file(
    chat_id: int,
    message_id: int
):
    """Delete an indexed file."""

    result = await files.delete_one(
        {
            "chat_id": chat_id,
            "message_id": message_id
        }
    )

    return result.deleted_count > 0


# =========================
# Total Files
# =========================

async def total_files():
    """Return total indexed files."""

    return await files.count_documents({})
