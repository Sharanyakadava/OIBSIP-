"""
database.py
SQLite persistence for the advanced chat app: users (with hashed
passwords), rooms, and message history. All operations are wrapped so
DB failures raise a clear DatabaseError instead of crashing the app.

Security note: message content is stored in PLAIN TEXT. Only account
passwords are hashed. See README.md's "Security & Privacy" section.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "chat.db")


class DatabaseError(Exception):
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
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        # A default room so there's always somewhere to chat.
        conn.execute(
            "INSERT OR IGNORE INTO rooms (name, created_by, created_at) VALUES (?, ?, ?)",
            ("general", "system", datetime.now().isoformat(timespec="seconds")),
        )


# ---- users ----

def create_user(username, password_hash):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, datetime.now().isoformat(timespec="seconds")),
            )
    except DatabaseError as e:
        if "UNIQUE constraint failed" in str(e):
            raise DatabaseError(f"Username '{username}' is already taken.") from e
        raise


def get_user_by_username(username):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None


# ---- rooms ----

def create_room(name, created_by):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO rooms (name, created_by, created_at) VALUES (?, ?, ?)",
                (name, created_by, datetime.now().isoformat(timespec="seconds")),
            )
    except DatabaseError as e:
        if "UNIQUE constraint failed" in str(e):
            raise DatabaseError(f"Room '{name}' already exists.") from e
        raise


def get_room_by_name(name):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM rooms WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None


def list_rooms():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM rooms ORDER BY name COLLATE NOCASE").fetchall()
        return [dict(r) for r in rows]


# ---- messages ----

def add_message(room_id, username, content):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO messages (room_id, username, content, created_at) VALUES (?, ?, ?, ?)",
            (room_id, username, content, datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def get_recent_messages(room_id, limit=50):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM (
                SELECT id, username, content, created_at
                FROM messages
                WHERE room_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
            ) ORDER BY created_at ASC, id ASC
            """,
            (room_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
