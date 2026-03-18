"""
Repository for support cases (CRUD).

Saves each case to yagona baza (SQLite) and allows updating
group_message_id after forwarding to Telegram group.
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
        screenshot_file_id: Optional[str] = None,
        suggested_solution: Optional[str] = None,
    ) -> Case:
        """
        Insert new case and return it with id and created_at.
        """
        with get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO support_cases (
                        telegram_user_id, telegram_username,
                        telegram_full_name, category, problem_text,
                        screenshot_file_id, suggested_solution, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open')
                    """,
                    (
                        telegram_user_id,
                        telegram_username,
                        telegram_full_name,
                        category,
                        problem_text,
                        screenshot_file_id,
                        suggested_solution,
                    ),
                )
                case_id = cur.lastrowid
                cur.execute(
                    """
                    SELECT id, created_at, telegram_user_id, telegram_username,
                           telegram_full_name, category, problem_text,
                           screenshot_file_id, suggested_solution, group_message_id, status
                    FROM support_cases WHERE id = ?
                    """,
                    (case_id,),
                )
                row = cur.fetchone()
            finally:
                cur.close()
        return Case.from_row(row)

    def set_group_message_id(self, case_id: int, group_message_id: int) -> None:
        """Update case with Telegram group message id after forward."""
        with get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE support_cases SET group_message_id = ? WHERE id = ?",
                    (group_message_id, case_id),
                )
            finally:
                cur.close()

    def get_by_id(self, case_id: int) -> Optional[Case]:
        """Fetch one case by id."""
        with get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT id, created_at, telegram_user_id, telegram_username,
                           telegram_full_name, category, problem_text,
                           screenshot_file_id, suggested_solution, group_message_id, status
                    FROM support_cases WHERE id = ?
                    """,
                    (case_id,),
                )
                row = cur.fetchone()
            finally:
                cur.close()
        return Case.from_row(row) if row else None
