import os


API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

DB_URI = os.getenv("DB_URI", "")
DB_NAME = os.getenv("DB_NAME", "AdvancedAutoFilterBot")

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))
FILE_CHANNEL = int(os.getenv("FILE_CHANNEL", "0"))

BOT_USERNAME = os.getenv("BOT_USERNAME", "")
UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL", "")

# Search settings
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "10"))
AUTO_DELETE = int(os.getenv("AUTO_DELETE", "300"))
