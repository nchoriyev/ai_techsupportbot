"""
Forward case to support Telegram group.

Har bitta case: vaqt, muammo turi, ariza beruvchi, screenshot(lar), taxminiy yechim —
barchasi chiroyli formatda telegram guruhga yuboriladi.
Ko'p screenshot bo'lsa, birinchisi caption bilan, qolganlari alohida yuboriladi.
"""

import logging
from typing import List, Optional

from telegram import Bot

import config
from database.models import Case, CaseCategory

logger = logging.getLogger(__name__)


def _topic_id_for_category(category: str) -> Optional[int]:
    """Get forum topic id for category (if group is forum)."""
    return config.SUPPORT_TOPICS.get(category)


def format_case_for_group(case: Case) -> str:
    """Format case as a rich text message for the support group."""
    emoji = CaseCategory.EMOJI.get(case.category, "📋")
    category_label = CaseCategory.LABELS.get(case.category, case.category)

    user_display = case.telegram_full_name or ""
    if case.telegram_username:
        user_display += f" (@{case.telegram_username})"
    if not user_display.strip():
        user_display = str(case.telegram_user_id)

    lines = [
        f"{'━' * 28}",
        f"🆕  YANGI ARIZA  •  Case #{case.id}",
        f"{'━' * 28}",
        "",
        f"📅  Vaqt: {case.created_at_str}",
        f"{emoji}  Turi: {category_label}",
        f"👤  Ariza beruvchi: {user_display.strip()}",
        "",
        f"📝  Muammo:",
        case.problem_text,
    ]

    if case.suggested_solution:
        lines.extend(["", "💡  AI taxminiy yechim:", case.suggested_solution])

    sc = case.screenshot_count
    if sc > 0:
        lines.extend(["", f"📎  Screenshotlar: {sc} ta"])

    lines.extend(["", f"{'━' * 28}", "📌  Status: Ochiq"])

    return "\n".join(lines)


def format_case_for_user(case: Case) -> str:
    """Format case confirmation message for the user (bot chat)."""
    emoji = CaseCategory.EMOJI.get(case.category, "📋")
    category_label = CaseCategory.LABELS.get(case.category, case.category)

    lines = [
        "✅  Arizangiz qabul qilindi!",
        "",
        f"🔢  Case: #{case.id}",
        f"{emoji}  Turi: {category_label}",
        f"📅  Vaqt: {case.created_at_str}",
    ]

    if case.suggested_solution:
        lines.extend(["", "💡  Taxminiy yechim:", case.suggested_solution])
    else:
        lines.extend([
            "",
            "⏳  Muammongiz ustida ishlayapmiz.",
            "Tez orada xabar beramiz!",
        ])

    lines.extend(["", "Arizangiz support guruhiga yuborildi."])

    return "\n".join(lines)


async def send_case_to_group(
    bot: Bot,
    case: Case,
) -> Optional[int]:
    """
    Send case to support group.
    Ko'p screenshot bo'lsa, birinchisi caption bilan, qolganlari alohida.
    Returns first group message id or None on failure.
    """
    chat_id = config.SUPPORT_GROUP_ID
    if not chat_id:
        logger.error("SUPPORT_GROUP_ID not configured.")
        return None

    topic_id = _topic_id_for_category(case.category)
    text = format_case_for_group(case)
    screenshots = _get_screenshot_list(case)

    try:
        first_msg_id = None
        if screenshots:
            msg = await bot.send_photo(
                chat_id=chat_id,
                photo=screenshots[0],
                caption=text[:1024],
                message_thread_id=topic_id or None,
            )
            first_msg_id = msg.message_id

            for extra_photo in screenshots[1:]:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=extra_photo,
                    message_thread_id=topic_id or None,
                )
        else:
            msg = await bot.send_message(
                chat_id=chat_id,
                text=text,
                message_thread_id=topic_id or None,
            )
            first_msg_id = msg.message_id

        logger.info("Case #%d sent to group (msg_id=%s).", case.id, first_msg_id)
        return first_msg_id
    except Exception as send_error:
        logger.exception("Failed to send case #%d to group: %s", case.id, send_error)
        return None


def _get_screenshot_list(case: Case) -> List[str]:
    """Extract list of screenshot file_ids from comma-separated string."""
    if not case.screenshot_file_ids:
        return []
    return [s.strip() for s in case.screenshot_file_ids.split(",") if s.strip()]
