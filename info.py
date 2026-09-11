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

# Channel(s) where movie/files are stored
# New format:
#   FILE_CHANNELS=-1001111111111,-1002222222222
#
# Old FILE_CHANNEL is still supported for compatibility.
FILE_CHANNELS = []
_raw_file_channels = os.getenv("FILE_CHANNELS", "").strip()

if _raw_file_channels:
    for item in _raw_file_channels.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            FILE_CHANNELS.append(int(item))
        except ValueError:
            pass

FILE_CHANNEL = int(
    os.getenv("FILE_CHANNEL", "0")
)

if not FILE_CHANNELS and FILE_CHANNEL:
    FILE_CHANNELS = [FILE_CHANNEL]

# Log channel
LOG_CHANNEL = int(
    os.getenv("LOG_CHANNEL", "0")
)

# Admins allowed to approve indexing requests.
# Format:
#   ADMINS=123456789,987654321
ADMINS = []
_raw_admins = os.getenv("ADMINS", "").strip()

if _raw_admins:
    for item in _raw_admins.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            ADMINS.append(int(item))
        except ValueError:
            pass

# Owner is always treated as an admin when OWNER_ID is configured.
if OWNER_ID and OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)


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


START_PIC = os.getenv(
    "START_PIC",
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
