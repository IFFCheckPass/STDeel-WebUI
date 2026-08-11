import sqlite3
import pandas as pd
from contextlib import contextmanager
from pathlib import Path
import os

_DEFAULT_DB = Path(__file__).resolve().parent.parent / "stdeel-backend" / "app.db"
DB_PATH = os.environ.get('STDEEL_DB_PATH', str(_DEFAULT_DB))


@contextmanager
def get_db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        yield conn
    finally:
        conn.close()


def query_df(sql, params=None):
    with get_db() as conn:
        return pd.read_sql_query(sql, conn, params=params or [])


def query_one(sql, params=None):
    with get_db() as conn:
        cursor = conn.execute(sql, params or [])
        row = cursor.fetchone()
        return row[0] if row else None
