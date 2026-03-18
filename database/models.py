"""
Data models for support cases.

CaseCategory: enum-like category keys used in bot and DB.
Case: dataclass representing one support case (vaqt, muammo turi,
      ariza beruvchi, screenshot, yechim).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union


class CaseCategory:
    """
    Muammo turlari (categories). Bot tugmalari va DB da shu qiymatlar ishlatiladi.
    """
    MDM = "mdm"
    PAYMENT = "payment"
    LOGIN = "login"
    OTHER = "other"

    ALL = (MDM, PAYMENT, LOGIN, OTHER)

    LABELS = {
        MDM: "MDM / Qurilma",
        PAYMENT: "To'lov / Qarz / Shartnoma",
        LOGIN: "Login / Kirish",
        OTHER: "Boshqa",
    }


@dataclass
class Case:
    """
    Yagona bazadagi bitta support case.
    """
    id: Optional[int]
    created_at: Union[datetime, str]
    telegram_user_id: int
    telegram_username: Optional[str]
    telegram_full_name: Optional[str]
    category: str
    problem_text: str
    screenshot_file_id: Optional[str]
    suggested_solution: Optional[str]
    group_message_id: Optional[int]
    status: str  # open, closed, etc.

    @classmethod
    def from_row(cls, row: tuple) -> "Case":
        """Build Case from DB row (id, created_at, telegram_user_id, ...)."""
        created_at = row[1]
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                pass
        return cls(
            id=row[0],
            created_at=created_at,
            telegram_user_id=row[2],
            telegram_username=row[3],
            telegram_full_name=row[4],
            category=row[5],
            problem_text=row[6],
            screenshot_file_id=row[7],
            suggested_solution=row[8],
            group_message_id=row[9],
            status=row[10] or "open",
        )
