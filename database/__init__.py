"""
Database package for Asaxiy Tech Support Bot.
SQLite-based case storage.
"""

from database.connection import get_connection, init_db
from database.models import Case, CaseCategory
from database.repo import CaseRepository

__all__ = ["get_connection", "init_db", "Case", "CaseCategory", "CaseRepository"]
