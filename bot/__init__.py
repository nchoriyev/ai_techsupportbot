"""
Telegram bot package for Asaxiy Tech Support.

Handlers: /start, category buttons, problem text/photo, avtomatik javob.
Keyboards: to'liq muammo turlari tugmalari.
Group: case va screenshot ni support guruhiga yuborish.
"""

from bot.handlers import setup_handlers
from bot.keyboards import get_category_keyboard, get_main_keyboard

__all__ = [
    "setup_handlers",
    "get_category_keyboard",
    "get_main_keyboard",
]
