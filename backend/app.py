import os
import yaml
import sqlite3
import requests
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler

DB = os.getenv("DB_PATH", "storage.db")
CONFIG = "config.yaml"

app = FastAPI(title="Uptime Monitor")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

def load_config():
    with open(CONFIG, "r") as f:
        return yaml.safe_load(f)

def db():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS status (
            url TEXT PRIMARY KEY,
            name TEXT,
            is_online INTEGER,
            last_downtime TEXT,
            last_error TEXT,
            last_checked TEXT
        )
    """)
    conn.commit()
    conn.close()

def check_target(t):
    now = datetime.now(timezone.utc).isoformat()
    online = 0
    error = None

    try:
        r = requests.get(t["url"], timeout=10)
        if r.status_code < 500:
            online = 1
        else:
            error = f"HTTP {r.status_code}"
    except requests.exceptions.Timeout:
        error = "Timeout"
    except requests.exceptions.RequestException:
        error = "Connection error"

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT is_online FROM status WHERE url = ?", (t["url"],))
    prev = cur.fetchone()

    last_downtime = None
    if online == 0 and (not prev or prev[0] == 1):
        last_downtime = now

    cur.execute("""
        INSERT INTO status (url, name, is_online, last_downtime, last_error, last_checked)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            is_online = excluded.is_online,
            last_downtime = COALESCE(excluded.last_downtime, status.last_downtime),
            last_error = excluded.last_error,
            last_checked = excluded.last_checked
    """, (
        t["url"], t["name"], online,
        last_downtime, error, now
    ))

    conn.commit()
    conn.close()

def run_checks():
    cfg = load_config()
    for t in cfg["targets"]:
        check_target(t)

@app.on_event("startup")
def startup():
    init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_checks,
        "interval",
        minutes=load_config()["check_interval_minutes"]
    )
    scheduler.start()

@app.get("/api/status")
def status():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, url, is_online, last_downtime, last_error
        FROM status
    """)
    rows = cur.fetchall()
    conn.close()

    cfg = load_config()

    return {
        "checked_every_minutes": cfg["check_interval_minutes"],
        "timezone": cfg["timezone"],
        "now": datetime.now(timezone.utc).isoformat(),
        "targets": [
            {
                "name": r[0],
                "url": r[1],
                "status": "Online" if r[2] else "Offline",
                "last_downtime": r[3] or "Downtime not detected",
                "error": r[4]
            } for r in rows
        ]
    }
