from motor.motor_asyncio import AsyncIOMotorClient

from info import DB_URI, DB_NAME


if not DB_URI:
    raise RuntimeError(
        "DB_URI environment variable is not set."
    )


# MongoDB connection
mongo_client = AsyncIOMotorClient(
    DB_URI,
    serverSelectionTimeoutMS=5000
)

# Database
db = mongo_client[DB_NAME]


# Collections
users = db["users"]
groups = db["groups"]
files = db["files"]
settings = db["settings"]


async def check_database():
    """Check MongoDB connection."""
    await mongo_client.admin.command("ping")
    return True
