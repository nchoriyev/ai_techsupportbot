"""
Forward case to support Telegram group.

Har bitta case: vaqt, muammo turi, ariza beruvchi, screenshot —
barchasi telegram guruhga yuboriladi (javob tizimi to'liq avtomatlashishi uchun).
"""

import logging
from datetime import datetime
from typing import Optional

from telegram import Bot
import config
from database.models import Case, CaseCategory

logger = logging.getLogger(__name__)


def _topic_id_for_category(category: str) -> Optional[int]:
    """Get forum topic id for category (if group is forum)."""
    return config.SUPPORT_TOPICS.get(category)


def _format_case_message(case: Case) -> str:
    """Format case for group: vaqt, muammo turi, ariza beruvchi, matn."""
    cat_label = CaseCategory.LABELS.get(case.category, case.category)
    time_str = case.created_at.strftime("%Y-%m-%d %H:%M") if case.created_at else ""
    user = case.telegram_full_name or case.telegram_username or str(case.telegram_user_id)
    lines = [
        f"Case #{case.id}",
        f"Vaqt: {time_str}",
        f"Muammo turi: {cat_label}",
        f"Ariza beruvchi: {user}",
        f"",
        f"Muammo: {case.problem_text}",
    ]
    if case.suggested_solution:
        lines.append(f"\nTaxminiy yechim: {case.suggested_solution}")
    return "\n".join(lines)


async def send_case_to_group(
    bot: Bot,
    case: Case,
    screenshot_file_id: Optional[str] = None,
) -> Optional[int]:
    """
    Send case to support group. If screenshot_file_id given, send photo with caption;
    else send text. Uses topic_id if group is forum.
    Returns group message id or None on failure.
    """
    chat_id = config.SUPPORT_GROUP_ID
    topic_id = _topic_id_for_category(case.category)
    text = _format_case_message(case)

    try:
        if screenshot_file_id:
            msg = await bot.send_photo(
                chat_id=chat_id,
                photo=screenshot_file_id,
                caption=text[:1024],
                message_thread_id=topic_id if topic_id else None,
            )
        else:
            msg = await bot.send_message(
                chat_id=chat_id,
                text=text,
                message_thread_id=topic_id if topic_id else None,
            )
        return msg.message_id
    except Exception as e:
        logger.exception("Failed to send case to group: %s", e)
        return None
