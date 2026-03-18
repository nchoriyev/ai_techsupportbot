"""
Chat history loader from source/messages.json.

Parses Telegram export format, extracts problem descriptions and
admin (Saidjamol Qosimxonov) responses for AI context.
"""

import json
import logging
from typing import Any, List, Optional

import config

logger = logging.getLogger(__name__)

# In-memory cache of parsed problem->answer pairs
_cached_pairs: Optional[List[dict]] = None


def _extract_text(entity: Any) -> str:
    """Extract plain text from message 'text' field (string or list of entities)."""
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
    """Check if message is from admin Saidjamol Qosimxonov."""
    from_id = (msg.get("from_id") or "").strip().lower()
    from_name = (msg.get("from") or "").strip().lower()
    admin_id = f"user{config.ADMIN_TG_ID}"
    # saidjamol qosimxonov (with possible invisible chars)
    return admin_id in from_id or "saidjamol" in from_name


def _load_and_parse_pairs() -> List[dict]:
    """
    Load messages.json and extract problem->admin reply pairs.
    Returns list of dicts: {problem: str, reply: str}
    """
    global _cached_pairs
    if _cached_pairs is not None:
        return _cached_pairs

    path = config.MESSAGES_JSON_PATH
    if not path.exists():
        logger.warning("Chat history not found: %s", path)
        _cached_pairs = []
        return _cached_pairs

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as load_error:
        logger.exception("Failed to load messages.json: %s", load_error)
        _cached_pairs = []
        return _cached_pairs

    raw_messages = data.get("messages") or []
    parsed = []
    for msg in raw_messages:
        if msg.get("type") != "message":
            continue
        text = _extract_text(msg.get("text") or "")
        if text:
            parsed.append({
                "text": text,
                "is_admin": _is_admin_message(msg),
            })

    # Build problem->reply pairs
    pairs = []
    index = 0
    while index < len(parsed):
        msg = parsed[index]
        if msg["is_admin"]:
            index += 1
            continue
        problem = msg["text"]
        # Look ahead for admin reply
        reply = None
        look_ahead = index + 1
        while look_ahead < len(parsed) and look_ahead < index + 5:
            next_msg = parsed[look_ahead]
            if next_msg["is_admin"] and next_msg["text"]:
                reply = next_msg["text"]
                break
            if not next_msg["is_admin"] and next_msg["text"]:
                break
            look_ahead += 1
        if reply and reply != "✅":
            pairs.append({"problem": problem, "reply": reply})
        index = look_ahead if reply else index + 1

    _cached_pairs = pairs
    logger.info("Loaded %d problem->reply pairs from chat history.", len(pairs))
    return pairs


def get_relevant_examples(
    problem_text: str,
    max_examples: int = 15,
    max_chars: int = 12000,
) -> str:
    """
    Build a context string of past problem->admin response pairs.
    Used as few-shot context for Azure OpenAI.
    """
    pairs = _load_and_parse_pairs()
    if not pairs:
        return "Misol topilmadi."

    # Take the last N pairs (most recent = most relevant)
    selected = pairs[-max_examples:]

    lines = []
    for pair in selected:
        lines.append(f"Muammo: {pair['problem']}\nAdmin javob: {pair['reply']}")

    combined = "\n\n---\n\n".join(lines)
    if len(combined) > max_chars:
        combined = combined[-max_chars:]
    return combined
