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
        conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            start_ts TEXT NOT NULL,
            end_ts TEXT,
            duration INTEGER
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

    incidents = get_incidents_for_period(url, since_iso)

    downtime = 0
    incidents_count = 0

    for inc in incidents:
        start = datetime.fromisoformat(inc["start_ts"])
        end = (
            datetime.fromisoformat(inc["end_ts"])
            if inc["end_ts"]
            else now
        )

        effective_start = max(start, since)
        effective_end = min(end, now)

        if effective_end > effective_start:
            downtime += (effective_end - effective_start).total_seconds()
            incidents_count += 1

    downtime = int(downtime)
    uptime = max(0, period_seconds - downtime)
    percent = round((uptime / period_seconds) * 100, 3)

    return {
        "uptime_percent": percent,
        "downtime_seconds": downtime,
        "incidents": incidents_count
    }



    # ---------- INCIDENTS LOG ----------

def get_open_incident(url):
    with get_conn() as conn:
        conn.row_factory = dict_factory
        return conn.execute(
            "SELECT * FROM incidents WHERE url = ? AND end_ts IS NULL",
            (url,)
        ).fetchone()

def start_incident(url):
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO incidents (url, start_ts) VALUES (?, ?)",
            (url, now)
        )

def close_incident(url):
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, start_ts FROM incidents WHERE url = ? AND end_ts IS NULL",
            (url,)
        ).fetchone()

        if not row:
            return

        start = datetime.fromisoformat(row[1])
        duration = int((now - start).total_seconds())

        conn.execute(
            """
            UPDATE incidents
            SET end_ts = ?, duration = ?
            WHERE id = ?
            """,
            (now.isoformat(), duration, row[0])
        )

def update_fail_count(url: str, count: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE sites SET fail_count = ? WHERE url = ?",
            (count, url)
        )

def get_incidents_for_period(url: str, since_iso: str):
    with get_conn() as conn:
        conn.row_factory = dict_factory
        return conn.execute(
            """
            SELECT start_ts, end_ts
            FROM incidents
            WHERE url = ?
              AND (
                end_ts IS NULL
                OR end_ts >= ?
              )
            """,
            (url, since_iso)
        ).fetchall()
    
def get_incidents(limit: int = 50):
    with get_conn() as conn:
        conn.row_factory = dict_factory
        return conn.execute(
            """
            SELECT url, start_ts, end_ts, duration
            FROM incidents
            ORDER BY start_ts DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()



