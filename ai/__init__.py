"""
AI package for Asaxiy Tech Support Bot.

Uses Azure OpenAI and chat history (source/messages.json) to:
- Classify problem category (MDM, Payment, Login, Other)
- Suggest solution from admin (Saidjamol Qosimxonov) responses.
"""

from ai.chat_history import load_chat_history, get_relevant_examples
from ai.support_ai import SupportAI

__all__ = [
    "load_chat_history",
    "get_relevant_examples",
    "SupportAI",
]
