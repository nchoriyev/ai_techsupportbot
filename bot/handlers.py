"""
Telegram bot handlers: /start, category buttons, problem input, AI reply, DB save, group forward.

Javob berish tizimi to'liq avtomatlashgan: foydalanuvchi muammoni yuboradi ->
kategoriya aniqlanadi -> yechim taklifi -> case bazaga va guruhga yuboriladi.
"""

import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ai.support_ai import SupportAI
from bot.group_sender import send_case_to_group
from bot.keyboards import get_category_keyboard, get_main_keyboard
from database import init_db, CaseRepository
from database.models import CaseCategory

logger = logging.getLogger(__name__)

# User state: (category, problem_text, screenshot_file_id)
USER_STATE = {}


def _user_key(update: Update) -> int:
    """Unique key for user (chat_id)."""
    if update.effective_chat and update.effective_chat.id:
        return update.effective_chat.id
    return 0


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start: welcome and show main keyboard."""
    if not update.message:
        return
    await update.message.reply_text(
        "Asaxiy texnik qo'llab-quvvatlash botiga xush kelibsiz. "
        "Muammoingizni yuborish uchun «Yangi ariza» tugmasini bosing yoki muammoni to'g'ridan-to'g'ri yozing.",
        reply_markup=get_main_keyboard(),
    )


async def request_or_problem_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles both 'Yangi ariza' (show category buttons) and problem text/photo.
    If user already chose category, collects problem and sends case.
    """
    if not update.message:
        return
    uid = _user_key(update)
    text = (update.message.text or "").strip()
    photo = update.message.photo
    screenshot_file_id = photo[-1].file_id if photo else None

    # Already chose category — this message is problem description
    if uid in USER_STATE and USER_STATE[uid].get("category"):
        USER_STATE[uid]["problem_text"] = text or "(skrinshot orqali)"
        USER_STATE[uid]["screenshot_file_id"] = USER_STATE[uid].get("screenshot_file_id") or screenshot_file_id
        await _process_and_send_case(update, context, uid)
        return

    if text == "Yangi ariza" or (not text and not screenshot_file_id):
        USER_STATE[uid] = {"category": None, "problem_text": "", "screenshot_file_id": None}
        await update.message.reply_text(
            "Muammo turini tanlang:",
            reply_markup=get_category_keyboard(),
        )
        return

    # Direct problem text or photo — run AI
    problem = text or "(skrinshot)"
    USER_STATE[uid] = {"category": None, "problem_text": problem, "screenshot_file_id": screenshot_file_id}
    await _process_with_ai(update, context, uid, problem, screenshot_file_id)


async def callback_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User selected category (inline button)."""
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("cat_"):
        return
    await query.answer()
    category = query.data.replace("cat_", "").strip()
    if category not in CaseCategory.ALL:
        category = CaseCategory.OTHER

    uid = _user_key(update)
    if uid not in USER_STATE:
        USER_STATE[uid] = {"category": None, "problem_text": "", "screenshot_file_id": None}
    USER_STATE[uid]["category"] = category

    await query.edit_message_text(
        "Muammoingizni batafsil yozing (yoki skrinshot yuboring). "
        "Keyin yuborish tugmasini bosing yoki «Yuborish» deb yozing."
    )


async def photo_only(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Photo (with or without caption): collect screenshot, use caption as problem text if present."""
    if not update.message or not update.message.photo:
        return
    uid = _user_key(update)
    screenshot_file_id = update.message.photo[-1].file_id
    caption = (update.message.caption or "").strip() or "(skrinshot orqali)"
    if uid in USER_STATE and USER_STATE[uid].get("category"):
        USER_STATE[uid]["problem_text"] = caption
        USER_STATE[uid]["screenshot_file_id"] = screenshot_file_id
        await _process_and_send_case(update, context, uid)
        return
    USER_STATE[uid] = {"category": None, "problem_text": caption, "screenshot_file_id": screenshot_file_id}
    await _process_with_ai(update, context, uid, caption, screenshot_file_id)


async def _process_with_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    uid: int,
    problem_text: str,
    screenshot_file_id: Optional[str],
) -> None:
    """Classify with AI, suggest solution, save case, send to group, reply to user."""
    support_ai = SupportAI()
    category, solution = support_ai.classify_and_suggest(problem_text)
    USER_STATE[uid] = {"category": category, "problem_text": problem_text, "screenshot_file_id": screenshot_file_id}

    user = update.effective_user
    repo = CaseRepository()
    case = repo.add(
        telegram_user_id=user.id if user else 0,
        category=category,
        problem_text=problem_text,
        telegram_username=user.username if user else None,
        telegram_full_name=user.full_name if user else None,
        screenshot_file_id=screenshot_file_id,
        suggested_solution=solution or None,
    )

    if context.bot:
        group_msg_id = await send_case_to_group(context.bot, case, screenshot_file_id)
        if group_msg_id:
            repo.set_group_message_id(case.id, group_msg_id)

    cat_label = CaseCategory.LABELS.get(category, category)
    reply = f"Muammo turi: {cat_label}\nCase #{case.id} qayd etildi va guruhga yuborildi."
    if solution:
        reply += f"\n\nTaxminiy yechim:\n{solution}"
    if update.message:
        await update.message.reply_text(reply)


async def _process_and_send_case(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    uid: int,
) -> None:
    """User already selected category; save case, send to group, clear state."""
    state = USER_STATE.get(uid)
    if not state or not state.get("category"):
        if update.message:
            await update.message.reply_text("Iltimos, avval muammo turini tanlang.", reply_markup=get_category_keyboard())
        return

    category = state["category"]
    problem_text = state.get("problem_text") or "(matn yuborilmadi)"
    screenshot_file_id = state.get("screenshot_file_id")

    user = update.effective_user
    repo = CaseRepository()
    case = repo.add(
        telegram_user_id=user.id if user else 0,
        category=category,
        problem_text=problem_text,
        telegram_username=user.username if user else None,
        telegram_full_name=user.full_name if user else None,
        screenshot_file_id=screenshot_file_id,
        suggested_solution=None,
    )

    if context.bot:
        group_msg_id = await send_case_to_group(context.bot, case, screenshot_file_id)
        if group_msg_id:
            repo.set_group_message_id(case.id, group_msg_id)

    cat_label = CaseCategory.LABELS.get(category, category)
    reply = f"Case #{case.id} qayd etildi va guruhga yuborildi.\nMuammo turi: {cat_label}"
    if update.message:
        await update.message.reply_text(reply)
    USER_STATE.pop(uid, None)


def setup_handlers(application: Application) -> None:
    """Register all handlers on the application."""
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, request_or_problem_message))
    application.add_handler(MessageHandler(filters.PHOTO, photo_only))
    application.add_handler(CallbackQueryHandler(callback_category, pattern="^cat_"))
    init_db()
