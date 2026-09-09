import re

from database import files


async def create_indexes():
    await files.create_index(
        [("chat_id", 1), ("message_id", 1)],
        unique=True,
        name="unique_file_message"
    )

    await files.create_index(
        [("search_name", 1)],
        name="search_name_index"
    )

    await files.create_index(
        [("file_name", "text")],
        name="file_name_text"
    )


async def save_file(file_data: dict):
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


def escape_regex(text: str) -> str:
    return re.escape(text.strip())


async def search_files(query: str, limit: int = 10):
    if not query:
        return []

    query = query.strip()

    if not query:
        return []

    safe_query = escape_regex(query)

    cursor = files.find(
        {
            "$or": [
                {
                    "search_name": {
                        "$regex": safe_query,
                        "$options": "i"
                    }
                },
                {
                    "file_name": {
                        "$regex": safe_query,
                        "$options": "i"
                    }
                },
                {
                    "caption": {
                        "$regex": safe_query,
                        "$options": "i"
                    }
                }
            ]
        }
    ).limit(limit)

    return await cursor.to_list(length=limit)


async def get_file(chat_id: int, message_id: int):
    return await files.find_one(
        {
            "chat_id": chat_id,
            "message_id": message_id
        }
    )


async def delete_file(chat_id: int, message_id: int):
    result = await files.delete_one(
        {
            "chat_id": chat_id,
            "message_id": message_id
        }
    )

    return result.deleted_count > 0


async def total_files():
    return await files.count_documents({})
