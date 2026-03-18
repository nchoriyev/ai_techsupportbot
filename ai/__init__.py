"""
AI package for Asaxiy Tech Support Bot.

Uses Azure OpenAI and chat history (source/messages.json) to:
- Classify problem category (MDM, Payment, Login, Other)
- Suggest solution from admin (Saidjamol Qosimxonov) responses.
"""

from ai.support_ai import SupportAI, get_support_ai

__all__ = ["SupportAI", "get_support_ai"]
