"""
Data models for support cases.

CaseCategory: enum-like category keys used in bot and DB.
Case: dataclass representing one support case.
ADMIN_CATEGORIES: admin tomonidan hal qilinadigan muammolar (faqat case yaratiladi).
INSTRUCTIONAL_CATEGORIES: AI ko'rsatma bera oladigan muammolar.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union


class CaseCategory:
    """Muammo turlari."""
    MDM = "mdm"
    PAYMENT = "payment"
    LOGIN = "login"
    OTHER = "other"

    ALL = (MDM, PAYMENT, LOGIN, OTHER)

    LABELS = {
        MDM: "📱 MDM / Qurilma",
        PAYMENT: "💳 To'lov / Qarz / Shartnoma",
        LOGIN: "🔐 Login / Kirish",
        OTHER: "📋 Boshqa",
    }

    EMOJI = {
        MDM: "📱",
        PAYMENT: "💳",
        LOGIN: "🔐",
        OTHER: "📋",
    }

    # Admin bajarishi kerak bo'lgan kategoriyalar — AI faqat case yaratadi
    ADMIN_ACTION = (PAYMENT,)

    # AI ko'rsatma bera oladigan kategoriyalar
    INSTRUCTIONAL = (MDM, LOGIN, OTHER)


@dataclass
class Case:
    """Yagona bazadagi bitta support case."""
    id: Optional[int]
    created_at: Union[datetime, str, None]
    telegram_user_id: int
    telegram_username: Optional[str]
    telegram_full_name: Optional[str]
    category: str
    problem_text: str
    screenshot_file_ids: Optional[str]  # comma-separated file_ids
    suggested_solution: Optional[str]
    group_message_id: Optional[int]
    status: str

    @property
    def created_at_str(self) -> str:
        if isinstance(self.created_at, datetime):
            return self.created_at.strftime("%Y-%m-%d %H:%M")
        if isinstance(self.created_at, str):
            return self.created_at[:16]
        return "—"

    @property
    def first_screenshot(self) -> Optional[str]:
        """First screenshot file_id (for sending to group)."""
        if self.screenshot_file_ids:
            return self.screenshot_file_ids.split(",")[0].strip()
        return None

    @property
    def screenshot_count(self) -> int:
        if not self.screenshot_file_ids:
            return 0
        return len([s for s in self.screenshot_file_ids.split(",") if s.strip()])

    @property
    def is_admin_action(self) -> bool:
        """This case requires admin action (not just instructions)."""
        return self.category in CaseCategory.ADMIN_ACTION

    @classmethod
    def from_row(cls, row) -> "Case":
        """Build Case from DB row (sqlite3.Row or tuple)."""
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
            screenshot_file_ids=row[7],
            suggested_solution=row[8],
            group_message_id=row[9],
            status=row[10] or "open",
        )
