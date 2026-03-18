"""
Telegram bot handlers — ConversationHandler + collecting buffer + group reaction.

KEY FEATURES:
1. Ko'p xabar/rasm yuborilsa — barchasi BITTA case ga yig'iladi (3 soniya buffer).
2. AI: instructional muammolarga yechim beradi; admin-action muammolarga
   "ustida ishlayapmiz" statusi qaytariladi.
3. Guruhda casega istalgan reaksiya (emoji) bosilsa — original userga
   bot orqali "muammongiz hal bo'ldi" xabari yuboriladi.
"""

import asyncio
import functools
import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    MessageReactionHandler,
    filters,
)

import config
from ai.support_ai import get_support_ai
from bot.group_sender import format_case_for_user, send_case_to_group
from bot.keyboards import (
    get_cancel_keyboard,
    get_category_keyboard,
    get_main_keyboard,
    get_done_keyboard,
)
from database import CaseRepository, init_db
from database.models import CaseCategory

logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_CATEGORY = 0
COLLECTING = 1  # user sends text/photos — 3s buffer collects them all

# Context keys
KEY_CATEGORY = "case_category"
KEY_TEXTS = "case_texts"       # list of text strings
KEY_PHOTOS = "case_photos"     # list of file_id strings
KEY_TIMER = "case_timer"       # asyncio.Task for buffer

COLLECT_SECONDS = 3  # wait this many seconds after last message before finalizing

WELCOME_TEXT = (
    "👋 Asaxiy texnik qo'llab-quvvatlash botiga xush kelibsiz!\n\n"
    "Bu bot orqali muammoingizni tez va qulay tarzda bildirishingiz mumkin.\n\n"
    "📝 «Yangi ariza» — muammo bildirib, yechim olish\n"
    "ℹ️ «Yordam» — bot qanday ishlaydi\n\n"
    "Yoki muammoingizni to'g'ridan-to'g'ri yozing — "
    "AI avtomatik kategoriyani aniqlaydi."
)

HELP_TEXT = (
    "ℹ️  Bot qanday ishlaydi?\n\n"
    "1️⃣  «📝 Yangi ariza» tugmasini bosing\n"
    "2️⃣  Muammo turini tanlang\n"
    "3️⃣  Muammoingizni batafsil yozing — matn, rasm,\n"
    "     bir nechta xabar yuborishingiz mumkin\n"
    "4️⃣  «✅ Yuborish» tugmasini bosing\n"
    "5️⃣  Bot AI yechim taklif qiladi (iloji bo'lsa)\n"
    "6️⃣  Arizangiz support guruhiga yuboriladi\n\n"
    "💡  To'g'ridan-to'g'ri matn yuborsangiz ham ishlaydi —\n"
    "bot avtomatik turini aniqlaydi.\n\n"
    "Admin: @Saidjamol_Qosimxonov"
)


def _clear_user_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear case-related user data."""
    timer = context.user_data.pop(KEY_TIMER, None)
    if timer and not timer.done():
        timer.cancel()
    for key in (KEY_CATEGORY, KEY_TEXTS, KEY_PHOTOS):
        context.user_data.pop(key, None)


def _init_collecting(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initialize collecting lists."""
    if KEY_TEXTS not in context.user_data:
        context.user_data[KEY_TEXTS] = []
    if KEY_PHOTOS not in context.user_data:
        context.user_data[KEY_PHOTOS] = []


# ──────────────────────────── /start ────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_user_data(context)
    if update.message:
        await update.message.reply_text(WELCOME_TEXT, reply_markup=get_main_keyboard())
    return ConversationHandler.END


# ──────────────────── Yangi ariza flow ──────────────────────

async def new_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """📝 Yangi ariza — show category buttons."""
    _clear_user_data(context)
    if update.message:
        await update.message.reply_text(
            "Muammo turini tanlang:",
            reply_markup=get_category_keyboard(),
        )
    return CHOOSING_CATEGORY


async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User tapped a category inline button."""
    query = update.callback_query
    if not query or not query.data:
        return CHOOSING_CATEGORY

    await query.answer()
    category = query.data.replace("cat_", "").strip()
    if category not in CaseCategory.ALL:
        category = CaseCategory.OTHER

    context.user_data[KEY_CATEGORY] = category
    _init_collecting(context)

    label = CaseCategory.LABELS.get(category, category)
    await query.edit_message_text(
        f"✅ Tanlandi: {label}\n\n"
        "Endi muammoingizni batafsil yozing.\n"
        "Bir nechta xabar va rasm yuborishingiz mumkin.\n"
        "Tayyor bo'lgach, «✅ Yuborish» tugmasini bosing.",
        reply_markup=get_done_keyboard(),
    )
    return COLLECTING


# ──────────────── Collecting (multiple messages) ────────────────

async def collect_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User sent text while collecting — add to buffer."""
    if not update.message:
        return COLLECTING

    text = (update.message.text or "").strip()
    if text:
        _init_collecting(context)
        context.user_data[KEY_TEXTS].append(text)

    return COLLECTING


async def collect_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User sent photo while collecting — add to buffer."""
    if not update.message or not update.message.photo:
        return COLLECTING

    _init_collecting(context)
    file_id = update.message.photo[-1].file_id
    context.user_data[KEY_PHOTOS].append(file_id)

    caption = (update.message.caption or "").strip()
    if caption:
        context.user_data[KEY_TEXTS].append(caption)

    return COLLECTING


async def done_collecting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User pressed ✅ Yuborish — finalize case."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("⏳ Ariza tayyorlanmoqda...")

    return await _finalize_case(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User pressed cancel."""
    _clear_user_data(context)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Ariza bekor qilindi.")
    elif update.message:
        await update.message.reply_text(
            "❌ Ariza bekor qilindi.", reply_markup=get_main_keyboard()
        )
    return ConversationHandler.END


# ──────────── Direct message (no button flow) ────────────

async def direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User sends text directly — AI classifies. Single message = single case."""
    if not update.message:
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    _clear_user_data(context)
    context.user_data[KEY_TEXTS] = [text]
    context.user_data[KEY_PHOTOS] = []

    await update.message.reply_text("⏳ AI muammo turini aniqlayapti...")
    await _finalize_case(update, context)


async def direct_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User sends photo directly — AI classifies from caption."""
    if not update.message or not update.message.photo:
        return

    _clear_user_data(context)
    file_id = update.message.photo[-1].file_id
    caption = (update.message.caption or "").strip() or "(skrinshot orqali)"

    context.user_data[KEY_TEXTS] = [caption]
    context.user_data[KEY_PHOTOS] = [file_id]

    await update.message.reply_text("⏳ AI muammo turini aniqlayapti...")
    await _finalize_case(update, context)


# ──────────────────── Finalize case ─────────────────────

async def _finalize_case(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """AI → DB → Group → User reply."""
    category = context.user_data.get(KEY_CATEGORY)
    texts = context.user_data.get(KEY_TEXTS, [])
    photos = context.user_data.get(KEY_PHOTOS, [])

    problem_text = "\n".join(texts).strip()
    screenshot_ids = ",".join(photos) if photos else None

    if not problem_text and not photos:
        target = _get_reply_target(update)
        if target:
            await target.reply_text(
                "❌ Muammo matni yoki rasm topilmadi.\nQaytadan urinib ko'ring.",
                reply_markup=get_main_keyboard(),
            )
        _clear_user_data(context)
        return ConversationHandler.END

    if not problem_text:
        problem_text = "(skrinshot orqali yuborildi)"

    # Run AI (non-blocking)
    support_ai = get_support_ai()
    loop = asyncio.get_running_loop()

    if category:
        suggested_solution = await loop.run_in_executor(
            None,
            functools.partial(support_ai.suggest_for_category, problem_text, category),
        )
    else:
        category, suggested_solution = await loop.run_in_executor(
            None,
            functools.partial(support_ai.classify_and_suggest, problem_text),
        )

    if not category:
        category = CaseCategory.OTHER

    # Save to DB
    user = update.effective_user
    repo = CaseRepository()
    case = repo.add(
        telegram_user_id=user.id if user else 0,
        category=category,
        problem_text=problem_text,
        telegram_username=user.username if user else None,
        telegram_full_name=user.full_name if user else None,
        screenshot_file_ids=screenshot_ids,
        suggested_solution=suggested_solution or None,
    )

    # Send to group
    if context.bot:
        group_msg_id = await send_case_to_group(context.bot, case)
        if group_msg_id:
            repo.set_group_message_id(case.id, group_msg_id)

    # Reply to user
    user_reply = format_case_for_user(case)
    target = _get_reply_target(update)
    if target:
        await target.reply_text(user_reply, reply_markup=get_main_keyboard())

    _clear_user_data(context)
    return ConversationHandler.END


def _get_reply_target(update: Update):
    """Get message object to reply to."""
    if update.callback_query and update.callback_query.message:
        return update.callback_query.message
    return update.message


# ──────────────────── Group reaction handler ─────────────────────

async def handle_group_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Guruhda casega istalgan reaksiya (emoji) bosilganda —
    original userga bot orqali "muammongiz hal bo'ldi" xabari yuboriladi.
    """
    logger.info("=== REACTION UPDATE RECEIVED ===")
    logger.info("Full update: %s", update)

    reaction = update.message_reaction
    if not reaction:
        logger.warning("No message_reaction in update.")
        return

    chat_id = reaction.chat.id if reaction.chat else None
    message_id = reaction.message_id
    logger.info(
        "Reaction: chat_id=%s, message_id=%s, new_reaction=%s, old_reaction=%s",
        chat_id, message_id, reaction.new_reaction, reaction.old_reaction,
    )

    group_id = config.SUPPORT_GROUP_ID
    if chat_id != group_id:
        logger.info("Skipping: chat_id %s != SUPPORT_GROUP_ID %s", chat_id, group_id)
        return

    new_reactions = reaction.new_reaction
    if not new_reactions:
        logger.info("Skipping: no new reactions (reaction removed).")
        return

    repo = CaseRepository()
    case = repo.get_by_group_message_id(message_id)
    if not case:
        logger.info("No case found for group_message_id=%d.", message_id)
        return

    if case.status == "closed":
        logger.info("Case #%d already closed.", case.id)
        return

    repo.close_case(case.id)
    logger.info("Case #%d closed. Notifying user %d...", case.id, case.telegram_user_id)

    try:
        await context.bot.send_message(
            chat_id=case.telegram_user_id,
            text=(
                f"✅ Muammongiz hal bo'ldi!\n\n"
                f"🔢 Case #{case.id}\n"
                f"{CaseCategory.EMOJI.get(case.category, '📋')} "
                f"{CaseCategory.LABELS.get(case.category, case.category)}\n\n"
                f"Agar yana muammo bo'lsa, «📝 Yangi ariza» bosing."
            ),
            reply_markup=get_main_keyboard(),
        )
        logger.info("User %d notified: case #%d resolved.", case.telegram_user_id, case.id)
    except Exception as notify_error:
        logger.exception(
            "Failed to notify user %d about case #%d: %s",
            case.telegram_user_id, case.id, notify_error,
        )


# ──────────────────── Help ─────────────────────

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(HELP_TEXT, reply_markup=get_main_keyboard())


# ──────────────────── Error handler ─────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Bot error: %s", context.error, exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
                reply_markup=get_main_keyboard(),
            )
        except Exception:
            pass


# ──────────────────── Setup ─────────────────────

def setup_handlers(application: Application) -> None:
    """Register all handlers on the application."""

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📝 Yangi ariza$"), new_request),
        ],
        states={
            CHOOSING_CATEGORY: [
                CallbackQueryHandler(category_chosen, pattern="^cat_"),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
            COLLECTING: [
                MessageHandler(filters.PHOTO, collect_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^(📝 Yangi ariza|ℹ️ Yordam)$"), collect_text),
                CallbackQueryHandler(done_collecting, pattern="^done$"),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True,
    )

    application.add_handler(conv)
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ Yordam$"), cmd_help))

    # Direct message/photo (outside conversation)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex("^(📝 Yangi ariza|ℹ️ Yordam)$"),
        direct_message,
    ))
    application.add_handler(MessageHandler(filters.PHOTO, direct_photo))

    # Group reaction handler — guruhda istalgan reaksiya bosilsa
    application.add_handler(MessageReactionHandler(
        handle_group_reaction,
        chat_id=config.SUPPORT_GROUP_ID,
    ))

    application.add_error_handler(error_handler)

    init_db()
