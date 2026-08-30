"""
Database connection management for SQLite.
Provides a context manager that ensures foreign keys are enabled.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Any


DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "salon_pos.db"


def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite connection with foreign keys enabled.
    The connection uses Row factory for dict-like access.
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class DBConnection:
    """
    Context manager for database connections.
    Automatically commits on success and rolls back on exception.
    """

    def __enter__(self) -> sqlite3.Connection:
        self.conn = get_db_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
        return False  # propagate exceptions