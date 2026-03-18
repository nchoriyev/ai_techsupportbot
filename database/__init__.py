"""
Database package for Asaxiy Tech Support Bot.

Provides connection pool, case model, and repository to store
support cases in PostgreSQL (yagona baza).
"""

from database.connection import get_connection, init_db
from database.models import Case, CaseCategory
from database.repo import CaseRepository

__all__ = [
    "get_connection",
    "init_db",
    "Case",
    "CaseCategory",
    "CaseRepository",
]
