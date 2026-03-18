"""
Support AI: category classification and solution suggestion using Azure OpenAI.

Ikki xil javob mantigi:
- INSTRUCTIONAL (mdm, login, other): AI ko'rsatma beradi — user o'zi bajarishi mumkin.
- ADMIN_ACTION (payment): Faqat case yaratiladi, userga "ustida ishlayapmiz" statusi qaytariladi.
"""

import json
import logging
import re
from typing import Optional, Tuple

from openai import AzureOpenAI

import config
from ai.chat_history import get_relevant_examples
from database.models import CaseCategory

logger = logging.getLogger(__name__)

_ai_instance: Optional["SupportAI"] = None


def get_support_ai() -> "SupportAI":
    """Return singleton SupportAI instance."""
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = SupportAI()
    return _ai_instance


class SupportAI:
    """Azure OpenAI client for classify + suggest."""

    def __init__(self) -> None:
        self._client: Optional[AzureOpenAI] = None
        if config.AZURE_OPENAI_ENDPOINT and config.AZURE_OPENAI_KEY:
            self._client = AzureOpenAI(
                api_key=config.AZURE_OPENAI_KEY,
                api_version=config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            )
            logger.info("Azure OpenAI client initialized.")
        else:
            logger.warning("Azure OpenAI not configured.")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def classify_and_suggest(self, problem_text: str) -> Tuple[str, str]:
        """
        Returns (category_key, suggested_solution).
        - Instructional categories: AI ko'rsatma beradi.
        - Admin-action categories: solution bo'sh qaytadi (handler o'zi status beradi).
        """
        if not self._client or not problem_text.strip():
            return CaseCategory.OTHER, ""

        context = get_relevant_examples(problem_text, max_examples=15, max_chars=10000)

        system_prompt = (
            "Siz Asaxiy kompaniyasi texnik qo'llab-quvvatlash yordamchisisiz.\n\n"
            "VAZIFA:\n"
            "1. Muammoni kategoriyaga ajrating:\n"
            "   - mdm — qurilma/MDM bilan bog'liq (blokirovka, sozlash)\n"
            "   - payment — to'lov, qarz, shartnoma, rassrochka, pul qaytarish\n"
            "   - login — kirish, parol, tizimga ulanish\n"
            "   - other — boshqa\n\n"
            "2. Agar muammo 'payment' kategoriyaga tegishli bo'lsa — "
            "bu admin (Saidjamol Qosimxonov) bajarishi kerak bo'lgan ish. "
            "solution maydonini BO'SH qoldiring (\"\").\n\n"
            "3. Agar muammo 'mdm', 'login' yoki 'other' bo'lsa — "
            "guruh chat tarixidagi admin javoblari asosida ANIQ, AMALIY ko'rsatma yozing. "
            "Foydalanuvchi nima qilish kerakligini qadam-baqadam tushuntiring.\n\n"
            "JSON formatda javob:\n"
            '{\"category\": \"...\", \"solution\": \"...\"}'
        )

        user_prompt = (
            f"=== GURUH CHAT TARIXIDAN MISOLLAR ===\n{context}\n\n"
            f"=== FOYDALANUVCHI MUAMMOSI ===\n{problem_text}\n\n"
            "category va solution ni JSON da qaytaring."
        )

        try:
            response = self._client.chat.completions.create(
                model=config.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
            )
            content = (response.choices[0].message.content or "").strip()
            logger.info("AI response received (%d chars)", len(content))
            return self._parse_response(content)
        except Exception as error:
            logger.exception("Azure OpenAI error: %s", error)
            return CaseCategory.OTHER, ""

    def suggest_for_category(self, problem_text: str, category: str) -> str:
        """
        Faqat yechim taklif qilish (kategoriya allaqachon tanlangan).
        Admin-action kategoriya bo'lsa bo'sh qaytaradi.
        """
        if category in CaseCategory.ADMIN_ACTION:
            return ""
        if not self._client or not problem_text.strip():
            return ""

        context = get_relevant_examples(problem_text, max_examples=12, max_chars=8000)

        system_prompt = (
            "Siz Asaxiy texnik qo'llab-quvvatlash yordamchisisiz.\n"
            "Muammoga guruh chat tarixidagi admin javoblari asosida "
            "ANIQ, AMALIY ko'rsatma yozing. Qadam-baqadam.\n"
            "Faqat yechim matnini qaytaring."
        )

        user_prompt = (
            f"Kategoriya: {category}\n\n"
            f"=== GURUH TARIXIDAN MISOLLAR ===\n{context}\n\n"
            f"=== MUAMMO ===\n{problem_text}\n\n"
            "Yechim:"
        )

        try:
            response = self._client.chat.completions.create(
                model=config.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=600,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as error:
            logger.exception("Azure OpenAI suggest error: %s", error)
            return ""

    def _parse_response(self, content: str) -> Tuple[str, str]:
        """Parse JSON from model."""
        category = CaseCategory.OTHER
        solution = ""

        json_match = re.search(r"\{.*?\}", content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                raw_cat = (data.get("category") or "other").strip().lower()
                if raw_cat in CaseCategory.ALL:
                    category = raw_cat
                solution = (data.get("solution") or "").strip()
            except (json.JSONDecodeError, AttributeError):
                pass

        # Admin-action bo'lsa solution ni tozalash
        if category in CaseCategory.ADMIN_ACTION:
            solution = ""

        if not solution and content and category not in CaseCategory.ADMIN_ACTION:
            solution = content[:500]

        return category, solution
