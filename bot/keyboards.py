"""
Telegram bot keyboards — chiroyli va tushunarli tugmalar.

Botda to'liq muammo turlari tugmalari — emoji bilan, tartibli.
"""

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from database.models import CaseCategory


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Doimiy pastki tugmalar."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📝 Yangi ariza")],
            [KeyboardButton("ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )


def get_category_keyboard() -> InlineKeyboardMarkup:
    """Muammo turlari inline tugmalari."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 MDM / Qurilma", callback_data=f"cat_{CaseCategory.MDM}")],
        [InlineKeyboardButton("💳 To'lov / Qarz / Shartnoma", callback_data=f"cat_{CaseCategory.PAYMENT}")],
        [InlineKeyboardButton("🔐 Login / Kirish", callback_data=f"cat_{CaseCategory.LOGIN}")],
        [InlineKeyboardButton("📋 Boshqa muammo", callback_data=f"cat_{CaseCategory.OTHER}")],
    ])


def get_done_keyboard() -> InlineKeyboardMarkup:
    """Yuborish va bekor qilish tugmalari (collecting state)."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yuborish", callback_data="done")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")],
    ])


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Faqat bekor qilish tugmasi."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")],
    ])
