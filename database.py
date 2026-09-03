"""
database.py
SQLite persistence layer for the BMI Calculator.
Handles all reads/writes and wraps every operation in error handling
so the Flask app never crashes on a DB failure.
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "bmi_records.db")


class DatabaseError(Exception):
    """Raised when a database operation fails, so the app layer can
    show a friendly message instead of a stack trace."""
    pass


@contextmanager
def get_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise DatabaseError(f"Database error: {e}") from e
    finally:
        if conn:
            conn.close()


def init_db():
    """Create the records table if it doesn't already exist."""
    try:
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bmi_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    weight_kg REAL NOT NULL,
                    height_m REAL NOT NULL,
                    bmi REAL NOT NULL,
                    category TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
                """
            )
    except DatabaseError as e:
        # Fatal at startup - re-raise so the app can decide what to do.
        raise e


def add_record(user_name, weight_kg, height_m, bmi, category):
    """Insert a new BMI record. Returns the new row id."""
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO bmi_records (user_name, weight_kg, height_m, bmi, category, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_name, weight_kg, height_m, bmi, category, datetime.now().isoformat(timespec="seconds")),
            )
            return cur.lastrowid
    except DatabaseError:
        raise


def get_all_user_names():
    """Return a sorted list of distinct user names that have records."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT user_name FROM bmi_records ORDER BY user_name COLLATE NOCASE"
            ).fetchall()
            return [r["user_name"] for r in rows]
    except DatabaseError:
        raise


def get_records_for_user(user_name):
    """Return all records for a user, oldest first (for trend charts)."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, user_name, weight_kg, height_m, bmi, category, recorded_at
                FROM bmi_records
                WHERE user_name = ?
                ORDER BY recorded_at ASC
                """,
                (user_name,),
            ).fetchall()
            return [dict(r) for r in rows]
    except DatabaseError:
        raise


def delete_record(record_id):
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM bmi_records WHERE id = ?", (record_id,))
    except DatabaseError:
        raise
