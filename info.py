import os


# =========================
# Telegram Bot Configuration
# =========================

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


# =========================
# MongoDB Configuration
# =========================

DB_URI = os.getenv("DB_URI", "")
DB_NAME = os.getenv(
    "DB_NAME",
    "AdvancedAutoFilterBot"
)


# =========================
# Bot Owner
# =========================

OWNER_ID = int(os.getenv("OWNER_ID", "0"))


# =========================
# Telegram Channels
# =========================

# Channel where movie/files are stored
FILE_CHANNEL = int(
    os.getenv("FILE_CHANNEL", "0")
)

# Log channel
LOG_CHANNEL = int(
    os.getenv("LOG_CHANNEL", "0")
)


# =========================
# Bot Information
# =========================

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    ""
)

UPDATE_CHANNEL = os.getenv(
    "UPDATE_CHANNEL",
    ""
)


# =========================
# Auto Filter Settings
# =========================

MAX_RESULTS = int(
    os.getenv("MAX_RESULTS", "10")
)

AUTO_DELETE = int(
    os.getenv("AUTO_DELETE", "300")
)


# =========================
# Force Subscribe
# =========================

FORCE_SUB_CHANNEL = os.getenv(
    "FORCE_SUB_CHANNEL",
    ""
)


# =========================
# Messages
# =========================

SPELLING_CHECK = (
    "നിങ്ങൾ നൽകിയ movie name കണ്ടെത്താനായില്ല.\n"
    "✍️ Spelling ഒന്ന് check ചെയ്ത് വീണ്ടും try ചെയ്യൂ."
)

NOT_RELEASED = (
    "നിങ്ങൾ ചോദിച്ചാ സിനിമ ഇതുവരെ റിലീസ് ആയിട്ടില്ല."
)

NOT_IN_DATABASE = (
    "നിങ്ങൾ ചോദിച്ചാ movie ഞങ്ങളുടെ ഡാറ്റബേസിൽ add ആയിട്ടില്ല."
)
