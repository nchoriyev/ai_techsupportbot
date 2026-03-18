"""
Database connection and initialization (SQLite).

Creates local SQLite database file and ensures
support_cases table exists (init_db).
"""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import config

logger = logging.getLogger(__name__)

# Local SQLite DB file in project root
DB_PATH = Path(config.PROJECT_ROOT) / "support.db"


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for a single SQLite connection.
    Yields connection; commits on success, rolls back on exception.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Create support_cases table if not exists.
    Safe to call on every startup.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS support_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                telegram_user_id INTEGER NOT NULL,
                telegram_username TEXT,
                telegram_full_name TEXT,
                category TEXT NOT NULL,
                problem_text TEXT NOT NULL,
                screenshot_file_id TEXT,
                suggested_solution TEXT,
                group_message_id INTEGER,
                status TEXT NOT NULL DEFAULT 'open'
            );
            CREATE INDEX IF NOT EXISTS idx_support_cases_created_at
                ON support_cases(created_at);
            CREATE INDEX IF NOT EXISTS idx_support_cases_category
                ON support_cases(category);
            """
        )
    logger.info("Database initialized (support_cases table ready).")
