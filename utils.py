import re
from typing import Optional


# =========================
# Text Cleaning
# =========================

def clean_text(text: str) -> str:
    """
    Clean text for movie searching.
    """

    if not text:
        return ""

    text = text.lower()

    # Replace common separators
    text = re.sub(r"[._\-]+", " ", text)

    # Remove brackets
    text = re.sub(r"[\[\](){}]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================
# File Name Cleaning
# =========================

def clean_file_name(file_name: str) -> str:
    """
    Remove common quality / release tags
    from a file name.
    """

    if not file_name:
        return ""

    name = clean_text(file_name)

    patterns = [
        r"\b\d{4}\b",
        r"\b480p\b",
        r"\b576p\b",
        r"\b720p\b",
        r"\b1080p\b",
        r"\b2160p\b",
        r"\b4k\b",
        r"\b8k\b",
        r"\bweb[- ]?dl\b",
        r"\bweb[- ]?rip\b",
        r"\bbluray\b",
        r"\bbrrip\b",
        r"\bhdrip\b",
        r"\bhdtv\b",
        r"\bwebrip\b",
        r"\bx264\b",
        r"\bx265\b",
        r"\bhevc\b",
    ]

    for pattern in patterns:
        name = re.sub(
            pattern,
            " ",
            name,
            flags=re.IGNORECASE
        )

    name = re.sub(r"\s+", " ", name)

    return name.strip()


# =========================
# Search Query
# =========================

def normalize_query(query: str) -> str:
    """
    Normalize user's movie search query.
    """

    if not query:
        return ""

    query = clean_text(query)

    # Remove common search words
    stop_words = {
        "movie",
        "film",
        "download",
        "please",
        "send",
        "me",
    }

    words = [
        word
        for word in query.split()
        if word not in stop_words
    ]

    return " ".join(words)


# =========================
# Filename Display
# =========================

def get_display_name(
    file_name: Optional[str]
) -> str:

    if not file_name:
        return "Unknown File"

    return file_name


# =========================
# File Size
# =========================

def humanbytes(size: int) -> str:
    """
    Convert bytes into readable size.
    """

    if not size:
        return "0 B"

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    ]

    size = float(size)

    for unit in units:

        if size < 1024:
            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} PB"


# =========================
# Safe Integer
# =========================

def safe_int(
    value,
    default: int = 0
) -> int:

    try:
        return int(value)

    except (
        TypeError,
        ValueError
    ):
        return default
