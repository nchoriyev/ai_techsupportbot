"""
Telegram bot keyboards (button layouts).

Botda to'liq muammo turlari tugmalari bo'lishi zarur —
shu modul barcha category tugmalarini beradi.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram import KeyboardButton

from database.models import CaseCategory


def get_category_keyboard() -> InlineKeyboardMarkup:
    """
    Inline keyboard: MDM, To'lov, Login, Boshqa.
    Har bir tugma callback_data da category key (mdm, payment, login, other).
    """
    buttons = [
        [
            InlineKeyboardButton(
                CaseCategory.LABELS[CaseCategory.MDM],
                callback_data=f"cat_{CaseCategory.MDM}",
            ),
            InlineKeyboardButton(
                CaseCategory.LABELS[CaseCategory.PAYMENT],
                callback_data=f"cat_{CaseCategory.PAYMENT}",
            ),
        ],
        [
            InlineKeyboardButton(
                CaseCategory.LABELS[CaseCategory.LOGIN],
                callback_data=f"cat_{CaseCategory.LOGIN}",
            ),
            InlineKeyboardButton(
                CaseCategory.LABELS[CaseCategory.OTHER],
                callback_data=f"cat_{CaseCategory.OTHER}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Reply keyboard: "Yangi ariza" va boshqa kerakli tugmalar.
    """
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Yangi ariza")]],
        resize_keyboard=True,
    )
