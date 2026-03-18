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

DB_PATH = Path(config.PROJECT_ROOT) / "support.db"


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for a single SQLite connection.
    Yields connection; commits on success, rolls back on exception.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if not exist. Safe to call on every startup."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS support_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                telegram_user_id INTEGER NOT NULL,
                telegram_username TEXT,
                telegram_full_name TEXT,
                category TEXT NOT NULL,
                problem_text TEXT NOT NULL,
                screenshot_file_ids TEXT,
                suggested_solution TEXT,
                group_message_id INTEGER,
                status TEXT NOT NULL DEFAULT 'open'
            );
            CREATE INDEX IF NOT EXISTS idx_cases_category
                ON support_cases(category);
            CREATE INDEX IF NOT EXISTS idx_cases_group_msg
                ON support_cases(group_message_id);
        """)
    logger.info("Database initialized.")
