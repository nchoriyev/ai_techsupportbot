"""
Support AI: category classification and solution suggestion using Azure OpenAI.

Uses chat history (get_relevant_examples) as context and returns
category (mdm/payment/login/other) and suggested solution text.
"""

import logging
from typing import Optional, Tuple

from openai import AzureOpenAI

import config
from ai.chat_history import get_relevant_examples
from database.models import CaseCategory

logger = logging.getLogger(__name__)


class SupportAI:
    """
    Azure OpenAI client for:
    1) Muammo turini aniqlash (category)
    2) Chat history asosida taxminiy yechim berish
    """

    def __init__(self) -> None:
        self._client: Optional[AzureOpenAI] = None
        if config.AZURE_OPENAI_ENDPOINT and config.AZURE_OPENAI_KEY:
            self._client = AzureOpenAI(
                api_key=config.AZURE_OPENAI_KEY,
                api_version=config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            )
        else:
            logger.warning("Azure OpenAI not configured; AI suggestions disabled.")

    def classify_and_suggest(self, problem_text: str) -> Tuple[str, str]:
        """
        Returns (category_key, suggested_solution).
        category_key is one of CaseCategory.ALL.
        If Azure is not configured, returns ("other", "").
        """
        if not self._client or not problem_text.strip():
            return CaseCategory.OTHER, ""

        # First get context from chat history (we don't know category yet; use 'other' for broad context)
        context = get_relevant_examples(problem_text, "other", max_examples=12, max_chars=10000)

        system = (
            "Siz Asaxiy texnik qo'llab-quvvatlash yordamchisisiz. "
            "Foydalanuvchi muammosini quyidagi kategoriyalardan biriga ajrating: "
            "mdm (qurilma/MDM), payment (to'lov, qarz, shartnoma), login (kirish/parol), other (boshqa). "
            "Keyin guruh chat tarixidagi o'xshash masalalar va admin javoblariga asosan qisqa, aniq yechim taklifini yozing. "
            "Javobni JSON da qaytaring: {\"category\": \"mdm|payment|login|other\", \"solution\": \"...\"}."
        )
        user = (
            f"Guruh tarixidan misollar:\n{context}\n\n"
            f"Foydalanuvchi muammosi:\n{problem_text}\n\n"
            "category va solution ni JSON da yozing."
        )

        try:
            response = self._client.chat.completions.create(
                model=config.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_tokens=800,
            )
            content = (response.choices[0].message.content or "").strip()
            return self._parse_response(content, problem_text)
        except Exception as e:
            logger.exception("Azure OpenAI error: %s", e)
            return CaseCategory.OTHER, ""

    def _parse_response(self, content: str, problem_text: str) -> Tuple[str, str]:
        """Parse JSON from model; fallback to other + empty solution."""
        import re
        category = CaseCategory.OTHER
        solution = ""

        # Try to extract JSON
        match = re.search(r"\{[^{}]*\"category\"[^{}]*\"solution\"[^{}]*\}", content, re.DOTALL)
        if match:
            try:
                import json
                data = json.loads(match.group())
                c = (data.get("category") or "other").strip().lower()
                if c in CaseCategory.ALL:
                    category = c
                solution = (data.get("solution") or "").strip()
            except Exception:
                pass
        if not solution and content:
            solution = content[:500]
        return category, solution
