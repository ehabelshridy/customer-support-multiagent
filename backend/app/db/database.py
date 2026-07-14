"""Small helper around sqlite3 so tools don't repeat connection boilerplate."""

import sqlite3
from contextlib import contextmanager

from app.config import DB_PATH


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def fetch_one(query: str, params: tuple = ()) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def execute(query: str, params: tuple = ()) -> None:
    with get_connection() as conn:
        conn.execute(query, params)
        conn.commit()
