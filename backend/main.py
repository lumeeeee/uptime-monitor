import json
import time
import threading
import sqlite3
import requests
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DB_FILE = "monitor.db"
CONFIG_FILE = "domains.json"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            url TEXT PRIMARY KEY,
            status TEXT,
            last_downtime TEXT,
            last_error TEXT,
            last_checked TEXT
        )
        """)

def check_site(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code >= 500:
            return "Offline", f"HTTP {r.status_code}"
        return "Online", None
    except requests.exceptions.Timeout:
        return "Offline", "timeout"
    except requests.exceptions.ConnectionError:
        return "Offline", "connection error"
    except Exception as e:
        return "Offline", str(e)

def monitor_loop():
    while True:
        config = load_config()
        interval = config["check_interval_seconds"]
        domains = config["domains"]

        with db() as conn:
            for url in domains:
                status, error = check_site(url)
                now = datetime.now(timezone.utc).isoformat()

                cur = conn.execute(
                    "SELECT status FROM sites WHERE url = ?",
                    (url,)
                ).fetchone()

                if status == "Offline":
                    conn.execute("""
                        INSERT INTO sites (url, status, last_downtime, last_error, last_checked)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(url) DO UPDATE SET
                            status=excluded.status,
                            last_downtime=excluded.last_downtime,
                            last_error=excluded.last_error,
                            last_checked=excluded.last_checked
                    """, (url, status, now, error, now))
                else:
                    conn.execute("""
                        INSERT INTO sites (url, status, last_checked)
                        VALUES (?, ?, ?)
                        ON CONFLICT(url) DO UPDATE SET
                            status=excluded.status,
                            last_checked=excluded.last_checked,
                            last_error=NULL
                    """, (url, status, now))

        time.sleep(interval)

@app.on_event("startup")
def start_monitor():
    init_db()
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()

@app.get("/api/status")
def status():
    with db() as conn:
        rows = conn.execute("""
            SELECT url, status, last_downtime, last_error, last_checked
            FROM sites
            ORDER BY url
        """).fetchall()

    return {
        "timezone": "UTC",
        "checked_every_seconds": load_config()["check_interval_seconds"],
        "data": [
            {
                "url": r[0],
                "status": r[1],
                "last_downtime": r[2] or "Downtime not detected",
                "error": r[3],
                "last_checked": r[4]
            }
            for r in rows
        ]
    }
