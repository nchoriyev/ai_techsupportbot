"""
Asaxiy Tech Support Telegram Bot — entry point.

Ishga tushirish: python main.py
Bot: support guruhiga keladigan muammolarni sort qiladi, yagona bazaga yozadi,
     AI orqali muammo turi va taxminiy yechim beradi, har bir case vaqt/muammo turi/
     ariza beruvchi/screenshot bilan guruhga yuboriladi. Javob tizimi to'liq avtomat.
"""

import asyncio
import logging
import sys

from telegram.ext import Application

import config
from bot.handlers import setup_handlers

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Build application, register handlers, start polling.

    Python 3.14 da event loop bo'lmaganligi haqida xato chiqmasligi uchun
    qo'lda yangi event loop yaratib, uni joriy loop sifatida o'rnatamiz.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(config.BOT_TOKEN).build()
    setup_handlers(app)
    logger.info("Bot started. Polling...")
    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query",
            "message_reaction",
            "message_reaction_count",
        ],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
