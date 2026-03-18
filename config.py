"""
Configuration module for Asaxiy Tech Support Telegram Bot.

Loads environment variables from .env and exposes them as typed settings.
Used by bot, database, and AI modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)


def _get(key: str, default: str = "") -> str:
    """Get env var or default."""
    return os.getenv(key, default).strip()


def _get_int(key: str, default: int = 0) -> int:
    """Get env var as int."""
    try:
        return int(_get(key) or default)
    except ValueError:
        return default


def _get_float(key: str, default: float = 0.0) -> float:
    """Get env var as float."""
    try:
        return float(_get(key) or default)
    except ValueError:
        return default


# ——— Bot ———
BOT_TOKEN = _get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env")

# ——— Database (PostgreSQL) ———
DB_HOST = _get("DB_HOST", "localhost")
DB_PORT = _get_int("DB_PORT", 5432)
DB_NAME = _get("DB_NAME", "asaxiy_support")
DB_USER = _get("DB_USER", "postgres")
DB_PASSWORD = _get("DB_PASSWORD")
DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ——— Support group and topics (forum topics) ———
SUPPORT_GROUP_ID = _get_int("SUPPORT_GROUP_ID")
SUPPORT_TOPIC_MDM = _get_int("SUPPORT_TOPIC_MDM", 13)
SUPPORT_TOPIC_PAYMENT = _get_int("SUPPORT_TOPIC_PAYMENT", 6)
SUPPORT_TOPIC_LOGIN = _get_int("SUPPORT_TOPIC_LOGIN", 16)
SUPPORT_TOPIC_OTHER = _get_int("SUPPORT_TOPIC_OTHER", 19)

# Topic ID by category key
SUPPORT_TOPICS = {
    "mdm": SUPPORT_TOPIC_MDM,
    "payment": SUPPORT_TOPIC_PAYMENT,
    "login": SUPPORT_TOPIC_LOGIN,
    "other": SUPPORT_TOPIC_OTHER,
}

# ——— Admin (Saidjamol Qosimxonov — muammolarni hal qiluvchi) ———
ADMIN_NAME = _get("ADMIN_NAME", "Saidjamol Qosimxonov")
ADMIN_USERNAME = _get("ADMIN_USERNAME", "Saidjamol_Qosimxonov")
ADMIN_TG_ID = _get_int("ADMIN_TG_ID", 1077771511)

# ——— AI (Azure OpenAI) ———
AZURE_OPENAI_ENDPOINT = _get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = _get("AZURE_OPENAI_KEY")
AZURE_OPENAI_DEPLOYMENT = _get("AZURE_OPENAI_DEPLOYMENT", "support-model")
AZURE_OPENAI_API_VERSION = _get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# ——— Matching thresholds (optional) ———
MIN_CONFIDENCE_HIGH = _get_float("MIN_CONFIDENCE_HIGH", 0.85)
MIN_CONFIDENCE_MEDIUM = _get_float("MIN_CONFIDENCE_MEDIUM", 0.40)
FUZZY_THRESHOLD = _get_int("FUZZY_THRESHOLD", 75)

# ——— Paths ———
PROJECT_ROOT = Path(__file__).resolve().parent
MESSAGES_JSON_PATH = PROJECT_ROOT / "source" / "messages.json"
