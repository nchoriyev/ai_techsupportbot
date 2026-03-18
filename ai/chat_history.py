"""
Chat history loader from source/messages.json.

Parses Telegram export format, extracts problem descriptions and
admin (Saidjamol Qosimxonov) responses for AI context.
"""

import json
import logging
from pathlib import Path
from typing import Any, List, Optional

import config

logger = logging.getLogger(__name__)

# In-memory cache of parsed messages
_cached_messages: Optional[List[dict]] = None


def _extract_text(entity: Any) -> str:
    """Extract plain text from message 'text' (string or list of entities)."""
    if isinstance(entity, str):
        return entity.strip()
    if isinstance(entity, list):
        parts = []
        for item in entity:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return " ".join(parts).strip()
    return ""


def _is_admin_message(msg: dict) -> bool:
    """Check if message is from admin Saidjamol Qosimxonov (from_id or from name)."""
    from_id = (msg.get("from_id") or "").strip().lower()
    from_name = (msg.get("from") or "").strip().lower()
    admin_id = f"user{config.ADMIN_TG_ID}"
    admin_name = config.ADMIN_NAME.lower()
    return admin_id in from_id or admin_name in from_name


def load_chat_history() -> List[dict]:
    """
    Load and parse source/messages.json.
    Returns list of message dicts with keys: id, date, from, from_id, text_plain, is_admin.
    """
    global _cached_messages
    if _cached_messages is not None:
        return _cached_messages

    path = config.MESSAGES_JSON_PATH
    if not path.exists():
        logger.warning("Chat history not found: %s", path)
        _cached_messages = []
        return _cached_messages

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.exception("Failed to load messages.json: %s", e)
        _cached_messages = []
        return _cached_messages

    messages = data.get("messages") or []
    result = []
    for m in messages:
        if m.get("type") != "message":
            continue
        text_plain = _extract_text(m.get("text") or "")
        result.append({
            "id": m.get("id"),
            "date": m.get("date"),
            "from": m.get("from"),
            "from_id": m.get("from_id"),
            "text_plain": text_plain,
            "is_admin": _is_admin_message(m),
        })
    _cached_messages = result
    logger.info("Loaded %d messages from chat history.", len(_cached_messages))
    return _cached_messages


def get_relevant_examples(
    problem_text: str,
    category: str,
    max_examples: int = 15,
    max_chars: int = 12000,
) -> str:
    """
    Build a context string of past problem->admin response pairs for the given category.
    Used as few-shot context for Azure OpenAI.
    """
    messages = load_chat_history()
    # Collect problem + admin reply pairs (simple: consecutive user -> admin)
    pairs: List[str] = []
    i = 0
    while i < len(messages) and len(pairs) < max_examples:
        msg = messages[i]
        text = (msg.get("text_plain") or "").strip()
        if not text or msg["is_admin"]:
            i += 1
            continue
        # User problem (often contains @Saidjamol or order id / link)
        problem = text
        reply = None
        j = i + 1
        while j < len(messages):
            next_msg = messages[j]
            next_text = (next_msg.get("text_plain") or "").strip()
            if next_msg["is_admin"] and next_text:
                reply = next_text
                break
            if not next_msg["is_admin"] and next_text:
                break
            j += 1
        if reply:
            pairs.append(f"Muammo: {problem}\nJavob: {reply}")
        i = j if reply else i + 1

    combined = "\n\n---\n\n".join(pairs[-max_examples:])
    if len(combined) > max_chars:
        combined = combined[-max_chars:]
    return combined or "Misol topilmadi."
