from datetime import datetime, timedelta, timezone
from .db import get_conn

def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

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
        conn.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            status TEXT NOT NULL,        -- online / offline
            timestamp TEXT NOT NULL      -- ISO UTC
        )
        """)



# ---------- SITES ----------

def get_all_sites():
    with get_conn() as conn:
        conn.row_factory = dict_factory
        return conn.execute("SELECT * FROM sites").fetchall()


def get_site(url: str):
    with get_conn() as conn:
        conn.row_factory = dict_factory
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
        conn.row_factory = dict_factory
        return conn.execute(
            """
            SELECT url, timestamp, error
            FROM downtime_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
    

    # ---------- STATUS HISTORY ----------

def insert_status_event(url: str, status: str, ts: str | None = None):
    from datetime import datetime, timezone
    if ts is None:
        ts = datetime.now(timezone.utc).isoformat()

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO status_history (url, status, timestamp) VALUES (?, ?, ?)",
            (url, status, ts)
        )


def get_status_events(url: str, since_iso: str):
    with get_conn() as conn:
        conn.row_factory = dict_factory
        return conn.execute(
            """
            SELECT status, timestamp
            FROM status_history
            WHERE url = ?
              AND timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (url, since_iso)
        ).fetchall()


def get_last_status_before(url: str, before_iso: str):
    with get_conn() as conn:
        conn.row_factory = dict_factory
        return conn.execute(
            """
            SELECT status, timestamp
            FROM status_history
            WHERE url = ?
              AND timestamp < ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (url, before_iso)
        ).fetchone()


def calculate_uptime(url: str, period_seconds: int):
    now = datetime.now(timezone.utc)
    since = now - timedelta(seconds=period_seconds)
    since_iso = since.isoformat()

    events = get_status_events(url, since_iso)
    prev = get_last_status_before(url, since_iso)

    timeline = []

    if prev:
        timeline.append({
            "status": prev["status"],
            "timestamp": since_iso
        })

    timeline.extend(events)

    if not timeline:
        return {
            "uptime_percent": 100.0,
            "downtime_seconds": 0,
            "incidents": 0
        }

    downtime = 0
    incidents = 0

    for i in range(len(timeline)):
        current = timeline[i]
        start = datetime.fromisoformat(current["timestamp"])

        if i + 1 < len(timeline):
            end = datetime.fromisoformat(timeline[i + 1]["timestamp"])
        else:
            end = now

        delta = (end - start).total_seconds()

        if current["status"] == "offline":
            downtime += delta
            incidents += 1

    uptime = max(0, period_seconds - downtime)
    percent = round((uptime / period_seconds) * 100, 3)

    return {
        "uptime_percent": percent,
        "downtime_seconds": int(downtime),
        "incidents": incidents
    }

