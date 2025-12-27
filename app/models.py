from datetime import datetime, timezone
from .db import get_conn


# ---------- INIT ----------

def create_tables():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            url TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            last_downtime TEXT,
            last_error TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS downtime_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            error TEXT
        )
        """)


# ---------- SITES ----------

def get_all_sites():
    with get_conn() as conn:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        return conn.execute("SELECT * FROM sites").fetchall()


def get_site(url: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM sites WHERE url = ?",
            (url,)
        ).fetchone()


def insert_site(url: str, status: str, error: str | None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sites (url, status, last_downtime, last_error) VALUES (?, ?, ?, ?)",
            (url, status, None, error)
        )


def update_site_status(url: str, status: str, error: str | None):
    with get_conn() as conn:
        conn.execute(
            "UPDATE sites SET status = ?, last_error = ? WHERE url = ?",
            (status, error, url)
        )


def mark_site_down(url: str, error: str):
    now = datetime.now(timezone.utc).isoformat()

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE sites
            SET status = ?, last_downtime = ?, last_error = ?
            WHERE url = ?
            """,
            ("offline", now, error, url)
        )

        conn.execute(
            """
            INSERT INTO downtime_log (url, timestamp, error)
            VALUES (?, ?, ?)
            """,
            (url, now, error)
        )


# ---------- DOWNTIME LOG ----------

def get_last_downtimes(limit: int = 30):
    with get_conn() as conn:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        return conn.execute(
            """
            SELECT url, timestamp, error
            FROM downtime_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
