"""
Repository for support cases (CRUD).

Saves each case to yagona baza (SQLite) and allows updating
group_message_id, looking up case by group_message_id, etc.
"""

import logging
from typing import Optional

from database.connection import get_connection
from database.models import Case

logger = logging.getLogger(__name__)


class CaseRepository:
    """CRUD for support_cases table."""

    def add(
        self,
        telegram_user_id: int,
        category: str,
        problem_text: str,
        telegram_username: Optional[str] = None,
        telegram_full_name: Optional[str] = None,
        screenshot_file_ids: Optional[str] = None,
        suggested_solution: Optional[str] = None,
    ) -> Case:
        """Insert new case and return it."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO support_cases (
                    telegram_user_id, telegram_username,
                    telegram_full_name, category, problem_text,
                    screenshot_file_ids, suggested_solution, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open')
                """,
                (
                    telegram_user_id, telegram_username,
                    telegram_full_name, category, problem_text,
                    screenshot_file_ids, suggested_solution,
                ),
            )
            case_id = cur.lastrowid
            cur.execute(
                """SELECT id, created_at, telegram_user_id, telegram_username,
                          telegram_full_name, category, problem_text,
                          screenshot_file_ids, suggested_solution,
                          group_message_id, status
                   FROM support_cases WHERE id = ?""",
                (case_id,),
            )
            row = cur.fetchone()
        return Case.from_row(row)

    def set_group_message_id(self, case_id: int, group_message_id: int) -> None:
        """Update case with Telegram group message id after forward."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE support_cases SET group_message_id = ? WHERE id = ?",
                (group_message_id, case_id),
            )

    def close_case(self, case_id: int) -> None:
        """Mark case as closed."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE support_cases SET status = 'closed' WHERE id = ?",
                (case_id,),
            )

    def get_by_id(self, case_id: int) -> Optional[Case]:
        """Fetch one case by id."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, created_at, telegram_user_id, telegram_username,
                          telegram_full_name, category, problem_text,
                          screenshot_file_ids, suggested_solution,
                          group_message_id, status
                   FROM support_cases WHERE id = ?""",
                (case_id,),
            )
            row = cur.fetchone()
        return Case.from_row(row) if row else None

    def get_by_group_message_id(self, group_message_id: int) -> Optional[Case]:
        """Fetch case by group_message_id (for reaction handler)."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, created_at, telegram_user_id, telegram_username,
                          telegram_full_name, category, problem_text,
                          screenshot_file_ids, suggested_solution,
                          group_message_id, status
                   FROM support_cases WHERE group_message_id = ?""",
                (group_message_id,),
            )
            row = cur.fetchone()
        return Case.from_row(row) if row else None
